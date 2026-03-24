"""
Oracle SDK v4.2 — Multi-tier research orchestrator (Claude Agent SDK).

  Phase 1: Smiths (N*10 parallel Haiku) -> tool access (Read, Grep, WebSearch, GitHub MCP)
  Phase 2: Anderson (N parallel Sonnet) -> each sees ONLY its chain's Smiths
  Multi-chain: all Anderson reports returned directly to Opus (no merger phase).

Prompts are piped via stdin as JSON. The calling session (Claude Code)
generates the prompts using its full conversation context — no Architect needed.

Fallback: if stdin is a TTY (no piped data), uses a built-in Architect (Sonnet)
to decompose the question.

Usage:
  /oracle question                          # Claude Code builds prompts, pipes them in
  echo '[...]' | python oracle_sdk.py       # direct stdin
  python oracle_sdk.py "question"           # fallback: Architect decomposes
"""

import asyncio
import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, field

from claude_agent_sdk import query, ClaudeAgentOptions

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Auto-clear CLAUDECODE env var so SDK can launch from inside a CC session
if "CLAUDECODE" in os.environ:
    del os.environ["CLAUDECODE"]

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
DEFAULT_CHAINS = 1
MAX_CHAINS = 8
SCOUTS_PER_CHAIN = 10
SCOUT_TIMEOUT_S = 300  # 5 min per Smith — kill hung agents
ANDERSON_TIMEOUT_S = 480  # 8 min per Anderson — Sonnet needs time, longest seen was 430s
# Max 20x credit system (source: oreateai.com reverse-engineering, ~Mar 2026)
# Credits = (input_tokens * model_weight) + (output_tokens * model_weight * 5)
# Output costs 5x input. Model weights: Haiku=0.2, Sonnet=1.0, Opus=1.67
# Anthropic can change these at any time — treat as approximate.
SESSION_CREDITS = 11_000_000    # Max 20x 5-hour session
WEEKLY_CREDITS = 83_330_000     # Max 20x 7-day rolling
OUTPUT_MULTIPLIER = 5           # output tokens cost 5x input
MODEL_WEIGHTS = {"haiku": 0.2, "sonnet": 1.0, "opus": 1.67}

SCOUT_SUFFIX = (
    "\n\nFor any specific number, state your source and confidence: "
    "HIGH (directly from source), MEDIUM (calculated/derived), LOW (estimated/extrapolated). "
    "Always note the date of your source. Prefer recent sources over older ones. "
    "If a stat is more than 12 months old, flag it as potentially outdated. "
    "Report findings only. You may include code snippets you find, but do NOT build or implement anything."
)


def _normalize_prompts(raw: list[dict]) -> list[dict]:
    """Auto-assign chain/id and append standard suffix if missing."""
    # Detect if chains are pre-assigned
    has_chains = any("chain" in p for p in raw)
    if has_chains:
        # Respect existing chain/id but append suffix
        for p in raw:
            if "_normalized" not in p:
                p["prompt"] += SCOUT_SUFFIX
                p["_normalized"] = True
        return raw

    # Streamlined format: just dimension + prompt
    # Validate: must be a multiple of 10
    if len(raw) % 10 != 0:
        print(f"  [oracle] WARNING: Got {len(raw)} prompts (not a multiple of 10). "
              f"Expected {((len(raw) // 10) + 1) * 10} for {(len(raw) // 10) + 1} chains.",
              file=sys.stderr)

    # Auto-assign chains of 10
    chains_count = max(1, len(raw) // 10)
    per_chain = 10 if len(raw) >= 10 else len(raw)

    prompts = []
    for i, p in enumerate(raw):
        chain = chr(65 + i // per_chain) if chains_count > 1 else "A"
        prompts.append({
            "chain": chain,
            "id": i + 1,
            "dimension": p["dimension"],
            "prompt": p["prompt"] + SCOUT_SUFFIX,
            "_normalized": True,
        })
    return prompts


# GitHub MCP — enabled when GITHUB_PAT env var is set (stdio transport only)
def _github_mcp() -> dict | None:
    pat = os.environ.get("GITHUB_PAT")
    if not pat:
        return None
    return {
        "github": {
            "command": "npx",
            "args": ["-yq", "@modelcontextprotocol/server-github"],
            "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": pat},
        }
    }


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class UsageStats:
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    quota_units: float = 0.0

    def add(self, other: "UsageStats"):
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens
        self.cost_usd += other.cost_usd
        self.quota_units += other.quota_units

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def session_pct(self) -> float:
        return (self.quota_units / SESSION_CREDITS) * 100 if SESSION_CREDITS else 0

    @property
    def weekly_pct(self) -> float:
        return (self.quota_units / WEEKLY_CREDITS) * 100 if WEEKLY_CREDITS else 0

    def __str__(self) -> str:
        return f"{self.total_tokens:,} tok ({self.weekly_pct:.2f}% weekly)"


@dataclass
class ScoutResult:
    scout_id: int
    chain: str
    dimension: str
    result_text: str
    error: str | None = None
    duration_ms: int = 0
    usage: UsageStats = field(default_factory=UsageStats)


@dataclass
class CompressorResult:
    chain: str
    summary: str
    error: str | None = None
    duration_ms: int = 0
    usage: UsageStats = field(default_factory=UsageStats)


@dataclass
class OracleMetrics:
    start_time: float = 0
    phase_times: dict = field(default_factory=dict)
    phase_usage: dict = field(default_factory=lambda: {
        "decompose": UsageStats(),
        "scout": UsageStats(),
        "compress": UsageStats(),
    })
    scout_count: int = 0
    scout_errors: int = 0
    compressor_count: int = 0
    compressor_errors: int = 0
    chain_count: int = 0

    @property
    def total_time(self) -> float:
        return time.time() - self.start_time if self.start_time else 0

    @property
    def total_usage(self) -> UsageStats:
        total = UsageStats()
        for u in self.phase_usage.values():
            total.add(u)
        return total


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_usage(message, model: str = "sonnet") -> UsageStats:
    """Extract usage stats and compute quota units based on model weight."""
    stats = UsageStats()
    if hasattr(message, "total_cost_usd") and message.total_cost_usd is not None:
        stats.cost_usd = message.total_cost_usd
    if hasattr(message, "usage") and message.usage is not None:
        usage = message.usage
        if hasattr(usage, "input_tokens"):
            stats.input_tokens = usage.input_tokens or 0
        elif isinstance(usage, dict):
            stats.input_tokens = usage.get("input_tokens", 0)
        if hasattr(usage, "output_tokens"):
            stats.output_tokens = usage.output_tokens or 0
        elif isinstance(usage, dict):
            stats.output_tokens = usage.get("output_tokens", 0)
    weight = MODEL_WEIGHTS.get(model, 1.0)
    stats.quota_units = (stats.input_tokens + stats.output_tokens * OUTPUT_MULTIPLIER) * weight
    return stats


# ---------------------------------------------------------------------------
# Oracle SDK
# ---------------------------------------------------------------------------
class OracleSDK:
    def __init__(
        self,
        chains: int = DEFAULT_CHAINS,
        verbose: bool = False,
        show_dollars: bool = False,
    ):
        if chains < 1 or chains > MAX_CHAINS:
            raise ValueError(f"Chains must be 1-{MAX_CHAINS}, got {chains}")
        self.chains = chains
        self.scouts_total = chains * SCOUTS_PER_CHAIN
        self.verbose = verbose
        self.show_dollars = show_dollars
        self.metrics = OracleMetrics()
        self._active_scouts: dict[int, str] = {}  # scout_id -> status
        self._has_architect = False  # set when Architect phase runs

    def log(self, msg: str):
        if self.verbose:
            print(f"  [oracle] {msg}", file=sys.stderr)

    def status(self, msg: str):
        """Always-on status line (not gated by verbose)."""
        print(f"  [oracle] {msg}", file=sys.stderr)

    def _phase(self, name: str) -> str:
        """Return 'Phase N/T -- name' with correct numbering."""
        order = []
        if self._has_architect:
            order.append("architect")
        order.append("smiths")
        order.append("anderson")
        idx = order.index(name) + 1
        return f"Phase {idx}/{len(order)} -- "

    # ----- Architect (fallback) -----

    async def decompose(self, question: str) -> list[dict]:
        """Fallback: use Sonnet to decompose question when no prompts piped via stdin."""
        self._has_architect = True
        self.status(f"{self._phase('architect')}Architect ({self.chains} chains of {SCOUTS_PER_CHAIN} Smiths)")
        t0 = time.time()

        chain_labels = [chr(65 + i) for i in range(self.chains)]  # A, B, C, ...

        prompt = f"""Decompose into exactly {self.scouts_total} sub-prompts across {self.chains} orthogonal chains ({', '.join(chain_labels)}).

QUESTION: {question}

Each sub-prompt: ONE dimension, DIFFERENT search terms, under 200 words.
Confidence/reporting instructions are auto-appended — don't include them.

Return ONLY a JSON array:
{{"chain": "A", "id": 1, "dimension": "short label", "prompt": "text"}}"""

        result_text = ""
        usage = UsageStats()
        async for message in query(
            prompt=prompt,
            options=ClaudeAgentOptions(
                model="sonnet",
                allowed_tools=["Read", "Grep", "Glob"],
                system_prompt="Decompose research questions into orthogonal sub-prompts. Output ONLY valid JSON.",
            ),
        ):
            if hasattr(message, "result"):
                result_text = message.result
                usage = _extract_usage(message, "sonnet")

        # Parse JSON from result
        text = result_text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        # Find the JSON array
        start = text.find("[")
        end = text.rfind("]") + 1
        if start >= 0 and end > start:
            text = text[start:end]

        prompts = json.loads(text)
        elapsed = time.time() - t0
        self.metrics.phase_times["decompose"] = elapsed
        self.metrics.phase_usage["decompose"] = usage
        self.status(f"  Architect designed {len(prompts)} Smiths ({elapsed:.1f}s) | {usage}")
        return prompts

    # ----- Phase 2: Scout -----

    async def _run_scout(self, scout_id: int, chain: str, dimension: str, prompt: str) -> ScoutResult:
        """Run a single Haiku scout with tool access."""
        t0 = time.time()
        self._active_scouts[scout_id] = "running"
        try:
            result_text = ""
            usage = UsageStats()
            last_tool = ""
            # Build MCP config if GitHub PAT is available
            tools = ["Read", "Grep", "Glob", "WebSearch", "WebFetch"]
            mcp = _github_mcp()
            opts = {
                "model": "haiku",
                "allowed_tools": tools,
                "disallowed_tools": ["Bash", "Write", "Edit", "NotebookEdit", "Agent"],
            }
            if mcp:
                opts["mcp_servers"] = mcp
                opts["allowed_tools"] = tools + ["mcp__github__*"]

            system = """Research scout. Search thoroughly, report findings concisely, do NOT speculate.

Be dense: facts, numbers, and sources. No filler, no restating the question, no introductions.
Tag every number with confidence: HIGH (primary source), MEDIUM (derived), LOW (estimated).
Flag all LOW-confidence numbers explicitly."""
            if mcp:
                system += """

GitHub MCP tools available — prefer these over WebSearch for repo data:
- mcp__github__search_repositories / search_code — find repos and code
- mcp__github__get_file_contents — read files from repos
- mcp__github__list_issues / list_commits — check activity"""

            async for message in query(
                prompt=prompt,
                options=ClaudeAgentOptions(
                    **opts,
                    system_prompt=system,
                ),
            ):
                if hasattr(message, "result"):
                    result_text = message.result
                    usage = _extract_usage(message, "haiku")
                elif hasattr(message, "last_tool_name") and message.last_tool_name:
                    new_tool = message.last_tool_name
                    if new_tool != last_tool:
                        last_tool = new_tool
                        self.log(f"  Smith #{scout_id} ({chain}/{dimension}): {new_tool}")

            self._active_scouts[scout_id] = "done"
            remaining = sum(1 for s in self._active_scouts.values() if s != "done")
            elapsed = time.time() - t0
            chain_prefix = f"{chain}/" if self.chains > 1 else ""
            self.status(f"  Smith #{scout_id} ({chain_prefix}{dimension}) done [{elapsed:.1f}s, {remaining} left]")

            return ScoutResult(
                scout_id=scout_id,
                chain=chain,
                dimension=dimension,
                result_text=result_text,
                duration_ms=int((time.time() - t0) * 1000),
                usage=usage,
            )
        except Exception as e:
            self._active_scouts[scout_id] = "error"
            self.status(f"  Smith #{scout_id} FAILED ({chain}/{dimension}): {e}")
            return ScoutResult(
                scout_id=scout_id,
                chain=chain,
                dimension=dimension,
                result_text="",
                error=str(e),
                duration_ms=int((time.time() - t0) * 1000),
            )

    async def scout(self, prompts: list[dict]) -> list[ScoutResult]:
        self.status(f"{self._phase('smiths')}Smiths ({self.scouts_total} Haiku, all parallel)")
        t0 = time.time()
        self._active_scouts = {}

        async def _scout_with_timeout(p: dict) -> ScoutResult:
            try:
                return await asyncio.wait_for(
                    self._run_scout(p["id"], p["chain"], p["dimension"], p["prompt"]),
                    timeout=SCOUT_TIMEOUT_S,
                )
            except asyncio.TimeoutError:
                self._active_scouts[p["id"]] = "timeout"
                remaining = sum(1 for s in self._active_scouts.values() if s not in ("done", "error", "timeout"))
                self.status(f"  Smith #{p['id']} ({p['dimension']}) TIMEOUT [{SCOUT_TIMEOUT_S}s, {remaining} left]")
                return ScoutResult(
                    scout_id=p["id"],
                    chain=p["chain"],
                    dimension=p["dimension"],
                    result_text="",
                    error=f"Timed out after {SCOUT_TIMEOUT_S}s",
                    duration_ms=SCOUT_TIMEOUT_S * 1000,
                )

        tasks = [_scout_with_timeout(p) for p in prompts]
        results = await asyncio.gather(*tasks)

        # Aggregate usage
        phase_usage = UsageStats()
        for r in results:
            if r.error:
                self.metrics.scout_errors += 1
            phase_usage.add(r.usage)

        self.metrics.scout_count = len(results)
        elapsed = time.time() - t0
        self.metrics.phase_times["scout"] = elapsed
        self.metrics.phase_usage["scout"] = phase_usage
        self.status(f"  {len(results)} Smiths returned ({elapsed:.1f}s), {self.metrics.scout_errors} errors | {phase_usage}")
        return results

    # ----- Phase 3: Compress -----

    async def _run_compressor(self, chain: str, scout_results: list[ScoutResult]) -> CompressorResult:
        """Run a single Sonnet compressor for one chain."""
        t0 = time.time()

        # Build the input: all scout results for this chain
        # Cap each Smith report to ~3K chars to prevent Anderson input from blowing up
        MAX_SMITH_CHARS = 8000
        truncated = []
        parts = []
        for r in scout_results:
            if r.error:
                continue
            text = r.result_text
            if len(text) > MAX_SMITH_CHARS:
                truncated.append(f"#{r.scout_id} ({len(text)} -> {MAX_SMITH_CHARS})")
                text = text[:MAX_SMITH_CHARS] + "... [truncated]"
            parts.append(f"--- Smith #{r.scout_id} ({r.dimension}) ---\n{text}")
        if truncated:
            self.log(f"  Truncated {len(truncated)} Smiths: {', '.join(truncated)}")
        scout_data = "\n\n".join(parts)
        error_scouts = [r for r in scout_results if r.error]
        if error_scouts:
            scout_data += "\n\n--- Errored Smiths ---\n" + "\n".join(
                f"Smith #{r.scout_id} ({r.dimension}): ERROR - {r.error}"
                for r in error_scouts
            )

        triage = """Triage rules:
- DEDUP: Merge overlapping findings, cite all source Smiths
- RECENCY: Conflicting numbers? Prefer the most recently dated source
- AGREE: Multiple Smiths converge = highest confidence
- DISAGREE: Flag genuine disputes (not just stale vs fresh data)
- GAPS: Note uncovered topics
- CORRECT: Fix obvious errors"""

        prompt = f"""Organize {len(scout_results)} Smith reports{f' (Chain {chain})' if self.chains > 1 else ''} for Opus synthesis.

{triage}

{scout_data}

IMPORTANT: Preserve all findings — do NOT cut for brevity. Your output goes directly to Opus.
Dedup overlapping facts, correct errors, flag disputes, but keep all unique signal.

Output: All findings (grouped by theme, with confidence + Smith #), Corrections, Disputes, Gaps.
Organize, don't compress — Opus will do the editorial judgment."""

        try:
            result_text = ""
            usage = UsageStats()
            async for message in query(
                prompt=prompt,
                options=ClaudeAgentOptions(
                    model="sonnet",
                    allowed_tools=["Read", "Grep", "Glob"],
                    system_prompt="You are Anderson. Organize Smith reports into structured findings. Preserve all unique signal — Opus handles final synthesis.",
                ),
            ):
                if hasattr(message, "result"):
                    result_text = message.result
                    usage = _extract_usage(message, "sonnet")

            elapsed_ms = int((time.time() - t0) * 1000)
            self.status(f"  Anderson {chain} done ({elapsed_ms / 1000:.1f}s) | {usage}")
            return CompressorResult(
                chain=chain,
                summary=result_text,
                duration_ms=elapsed_ms,
                usage=usage,
            )
        except Exception as e:
            self.status(f"  Anderson {chain} FAILED: {e}")
            return CompressorResult(
                chain=chain,
                summary="",
                error=str(e),
                duration_ms=int((time.time() - t0) * 1000),
            )

    async def compress(self, scout_results: list[ScoutResult]) -> list[CompressorResult]:
        """Dispatch one Sonnet compressor per chain — each sees ONLY its chain's data."""
        if self.chains == 1:
            self.status(f"{self._phase('anderson')}Anderson (1 Sonnet)")
        else:
            self.status(f"{self._phase('anderson')}Anderson ({self.chains} parallel Sonnet)")
        t0 = time.time()

        # Group scouts by chain
        chains: dict[str, list[ScoutResult]] = {}
        for r in scout_results:
            chains.setdefault(r.chain, []).append(r)

        # Launch one compressor per chain — TRUE ISOLATION
        # Each compressor receives ONLY its own chain's scout results
        async def _compress_with_timeout(chain: str, scouts: list, delay: float = 0) -> CompressorResult:
            if delay > 0:
                await asyncio.sleep(delay)
            try:
                return await asyncio.wait_for(
                    self._run_compressor(chain, scouts),
                    timeout=ANDERSON_TIMEOUT_S,
                )
            except asyncio.TimeoutError:
                self.status(f"  Anderson {chain} TIMEOUT [{ANDERSON_TIMEOUT_S}s]")
                return CompressorResult(
                    chain=chain,
                    summary="",
                    error=f"Timed out after {ANDERSON_TIMEOUT_S}s",
                    duration_ms=ANDERSON_TIMEOUT_S * 1000,
                )

        # Multi-chain: 3s base delay + 2s stagger to avoid subprocess race condition
        # Single chain: no stagger needed (no contention)
        tasks = [
            _compress_with_timeout(chain, scouts, delay=(3 + i * 2) if len(chains) > 1 else 0)
            for i, (chain, scouts) in enumerate(sorted(chains.items()))
        ]
        results = await asyncio.gather(*tasks)

        phase_usage = UsageStats()
        for r in results:
            if r.error:
                self.metrics.compressor_errors += 1
            phase_usage.add(r.usage)

        self.metrics.compressor_count = len(results)
        self.metrics.chain_count = len(chains)
        elapsed = time.time() - t0
        self.metrics.phase_times["compress"] = elapsed
        self.metrics.phase_usage["compress"] = phase_usage
        self.status(f"  {len(results)} Andersons returned ({elapsed:.1f}s) | {phase_usage}")
        return results

    # ----- Main orchestration -----

    async def run(self, question: str, prompts: list[dict] | None = None) -> str:
        """Execute the full oracle v4.2 protocol with true isolation."""
        self.metrics = OracleMetrics(start_time=time.time())

        if prompts:
            # Prompts provided by caller (Claude Code session) — skip Architect
            self.scouts_total = len(prompts)
            self.chains = len(set(p["chain"] for p in prompts))
        else:
            # Fallback: use built-in Architect to decompose
            prompts = await self.decompose(question)

        # Phase 2: Scout (all parallel)
        scout_results = await self.scout(prompts)

        # Guard: if all scouts failed, skip Anderson entirely
        successful_scouts = [r for r in scout_results if not r.error]
        if not successful_scouts:
            self.status("  WARNING: All Smiths failed or timed out. Skipping Anderson.")
            report = "ERROR: All Smiths failed or timed out. No data to synthesize."
        else:
            # Phase 3: Compress (one per chain, parallel, isolated)
            # TRUE ISOLATION: Python groups by chain. Each compressor sees ONLY its chain.
            compressor_results = await self.compress(scout_results)

            if not compressor_results:
                report = "ERROR: No compressor results"
            elif self.chains == 1:
                report = compressor_results[0].summary
            else:
                # Multi-chain: return all Anderson reports directly to the Opus session.
                chain_reports = []
                for r in compressor_results:
                    if not r.error:
                        chain_reports.append(f"{'=' * 60}\n## Chain {r.chain} — Anderson Report\n{'=' * 60}\n\n{r.summary}")
                    else:
                        chain_reports.append(f"## Chain {r.chain} — ERROR: {r.error}")
                report = "\n\n".join(chain_reports)

        # Append metrics footer
        m = self.metrics
        total = m.total_usage
        parts = []
        if self._has_architect:
            parts.append("Architect")
        parts.append(f"{self.scouts_total} Smiths")
        parts.append(f"{self.chains} Anderson{'s' if self.chains > 1 else ''}")
        parts.append("Opus (you)")
        arch = " -> ".join(parts)
        if self.show_dollars:
            cost_line = f"- Total cost: ${total.cost_usd:.4f}"
            phase_costs = ' | '.join(f'{k}: ${u.cost_usd:.4f}' for k, u in m.phase_usage.items())
        else:
            cost_line = f"- Quota: {total.weekly_pct:.2f}% weekly ({total.session_pct:.1f}% session)"
            phase_costs = ' | '.join(f'{k}: {u.weekly_pct:.2f}%' for k, u in m.phase_usage.items())
        footer = f"""

---
**Oracle SDK Execution Metrics**
- Architecture: {arch}
- Total time: {m.total_time:.0f}s
- Total tokens: {total.total_tokens:,} (in: {total.input_tokens:,} | out: {total.output_tokens:,})
{cost_line}
- Smiths: {m.scout_count} ({m.scout_errors} errors)
- Andersons: {m.compressor_count} ({m.compressor_errors} errors)
- Phase timing: {' | '.join(f'{k}: {v:.0f}s' for k, v in m.phase_times.items())}
- Phase costs: {phase_costs}
"""
        return report + footer


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
async def main():
    parser = argparse.ArgumentParser(
        description="Oracle SDK — Multi-tier research orchestrator with true isolation"
    )
    parser.add_argument("question", nargs="?", default="", help="Research question (required if no prompts piped via stdin)")
    parser.add_argument("--chains", "-c", type=int, default=DEFAULT_CHAINS,
        help=f"Number of chains for fallback Architect mode, 1-{MAX_CHAINS} (default: {DEFAULT_CHAINS})")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show real-time tool activity per scout")
    parser.add_argument("--usd", action="store_true", help="Show costs in USD instead of quota %%")
    parser.add_argument(
        "--report", "-r", action="store_true",
        help="Save report to a dated file in addition to stdout"
    )
    args = parser.parse_args()

    # Check for piped prompts on stdin
    prompts = None
    if not sys.stdin.isatty():
        stdin_data = sys.stdin.read().strip()
        if stdin_data:
            try:
                raw = json.loads(stdin_data)
            except json.JSONDecodeError as e:
                print(f"ERROR: Invalid JSON on stdin: {e}", file=sys.stderr)
                sys.exit(1)
            prompts = _normalize_prompts(raw)

    if not prompts and not args.question:
        parser.error("Either pipe prompts via stdin or provide a question argument")

    oracle = OracleSDK(
        chains=len(set(p["chain"] for p in prompts)) if prompts else args.chains,
        verbose=args.verbose,
        show_dollars=args.usd,
    )

    # Banner
    n_smiths = len(prompts) if prompts else SCOUTS_PER_CHAIN
    n_chains = oracle.chains
    parts = []
    if not prompts:
        parts.append("Architect")
    parts.append(f"{n_smiths} Smiths")
    parts.append(f"{n_chains} Anderson{'s' if n_chains > 1 else ''}")
    parts.append("Opus (you)")
    print(f"Oracle SDK v4.2 -- {' -> '.join(parts)}", file=sys.stderr)

    report = await oracle.run(args.question, prompts=prompts)

    print(report)

    if args.report:
        import datetime
        filename = f"oracle-report-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\nReport saved to: {filepath}", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())
