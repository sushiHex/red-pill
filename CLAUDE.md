# Red Pill — Claude Code Plugin

Multi-tier research orchestrator + semantic knowledge base.

## Stack
- Python 3.10+ only. No shell scripts, no Node dependency for the plugin itself
  (Node/npx is optional at runtime, only for Oracle's `GITHUB_PAT`-gated GitHub MCP).
- Plugin format: `.claude-plugin/plugin.json`
- Oracle and Mainframe are external dependencies (`claude-oracle`, `mainframe-mcp`
  — both on GitHub only, not PyPI), not vendored code. See docs/red-pill-system-overview.md.

## Structure
```
.claude-plugin/plugin.json   ← Plugin manifest
.mcp.json                    ← Registers mainframe-mcp (python -m mainframe_mcp.server)
configs/cpu-only.json        ← Seeded to ~/.claude/mainframe/config.json on first run
hooks/hooks.json             ← SessionStart: runs scripts/session_start.py
scripts/session_start.py     ← Installs claude-oracle + mainframe-mcp if missing, mkdir, seed config
scripts/sync.py              ← DEV ONLY: copy skills/+agents/ into ~/.claude/ for local testing
agents/                      ← agent-smith, agent-jones, agent-brown
skills/
  oracle/                    ← unmodified copy of claude-oracle's own SKILL.md
  mainframe-retrieval/       ← unmodified copy of mainframe-mcp's own SKILL.md (ambient, no slash command)
  red-pill/                  ← /red-pill project initialization
```

## Conventions
- Plugin names are kebab-case
- Skills reference Mainframe at `~/.claude/mainframe/`, not hardcoded user paths
- `.mcp.json` uses `${HOME}` for cross-platform paths
- `skills/oracle/SKILL.md` and `skills/mainframe-retrieval/SKILL.md` are copies of
  those projects' own bundled skill docs — **never edit them here.** Fix upstream
  in `claude-oracle`/`mainframe-mcp`, then re-copy the file verbatim into this repo.
- All executable logic lives in `scripts/*.py`. `hooks.json`/`.mcp.json` only ever
  invoke `python` — never add a `.sh` file or an inline shell one-liner for
  anything beyond that single `python <script>` invocation.

## Gotchas
- Neither `claude-oracle` nor `mainframe-mcp` is on PyPI — the SessionStart hook
  installs both via `pip install git+https://github.com/sushiHex/<repo>.git`,
  which needs `git` and network access at first-session time.
- `mainframe-mcp`'s core dependencies (`bitsandbytes`, `accelerate`,
  `sentence-transformers`, `lancedb`, `pylance`, `tantivy`) install unconditionally
  regardless of which config is selected — first install is much heavier than the
  old bundled `mcp-local-rag` backend was. `bitsandbytes` in particular can be
  finicky without a CUDA GPU; the seeded `configs/cpu-only.json` avoids needing
  one at *runtime*, but does not avoid installing it.
- No postInstall hooks in plugin system — use SessionStart hook instead
- `${CLAUDE_PLUGIN_ROOT}` not available in SKILL.md text — only in hooks and .mcp.json
- `scripts/sync.py` merges into `~/.claude/{skills,agents}` (`dirs_exist_ok=True`),
  it does not wipe the destination first. Verified: a file already present in a
  destination skill dir (e.g. the `claude-oracle` pip package's installed shim)
  survives a re-sync untouched. This used to be a real hazard when `skills/oracle/`
  bundled a full fork — resolved by depending on claude-oracle instead (see git log).
