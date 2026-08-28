# Red Pill System Overview

Red Pill is a local-only research and knowledge management ecosystem for Claude Code. It combines a multi-tier agent orchestrator (Oracle), a semantic knowledge base (Mainframe), and a project initialization tool — all delivered as a Claude Code plugin.

## Architecture

```
User question → /oracle [N] → Opus decomposes into N*10 sub-prompts
→ N*10 Haiku Smiths search in parallel (WebSearch, GitHub MCP, Read, Grep)
→ N Sonnet Andersons organize findings (one per chain, isolated)
→ Opus synthesizes → Report auto-saved to Mainframe
```

## Components

### Oracle (`/oracle [N] <question>`)
Multi-tier research orchestrator. Engine: the independent [claude-oracle](https://github.com/sushiHex/claude-oracle) pip package (installed by the SessionStart hook; Red Pill's `skills/oracle/SKILL.md` is a thin, unmodified copy of that package's own skill doc). Default 1 chain = 10 Smiths + 1 Anderson. Scaling: `/oracle 4` = 40 Smiths + 4 Andersons. Cost: 10 Haiku Smiths ≈ 0.17 Opus-equivalents.

### Mainframe (ambient skill, no slash command)
Local semantic knowledge base at `~/.claude/mainframe/`, served by the independent [mainframe-mcp](https://github.com/sushiHex/mainframe-mcp) package (installed by the SessionStart hook, registered in `.mcp.json` via `python -m mainframe_mcp.server`). Indexes all project `research/`, `docs/`, and `CLAUDE.md` files. Loads automatically via the `mainframe-retrieval` skill (also an unmodified copy from that repo) rather than an explicit `/mainframe` command. First run seeds a CPU-only config (`configs/cpu-only.json`, `BAAI/bge-small-en-v1.5`) if `~/.claude/mainframe/config.json` doesn't already exist.

### Red Pill (`/red-pill`)
Project initialization. Scans codebase, searches Mainframe for conventions, generates/audits CLAUDE.md. Also: `/red-pill status` for health checks.

### Standalone Agents
- agent-smith (Opus) — deep multi-round research
- agent-jones (Sonnet) — standard queries
- agent-brown (Haiku) — quick lookups

## Key Constraints
- Oracle and Mainframe are NOT vendored — Red Pill depends on their own repos
  (`claude-oracle`, `mainframe-mcp`) via `pip install git+https://...` in the
  SessionStart hook. Neither is on PyPI. Never re-fork their skill/engine files
  into this repo — fix upstream, then re-copy the unmodified skill doc here.
- `mainframe-mcp`'s dependencies (`bitsandbytes`, `accelerate`,
  `sentence-transformers`, `lancedb`, …) install unconditionally, even with the
  CPU-only config — first install is heavier than the old bundled backend.
- HTTP MCP broken in SDK v0.1.48 — stdio only
- Built-in subagents can't access MCP — use `gh` CLI via Bash
- Anderson stagger: 3s base + 2s per agent (multi-chain only) prevents subprocess race condition
- Smith prompts: ONE narrow question, under 150 words, multiple of 10

## Distribution
- Plugin: `github.com/sushiHex/red-pill` (private)
- Dependencies (both public, installed from GitHub — neither is on PyPI):
  - `github.com/sushiHex/claude-oracle`
  - `github.com/sushiHex/mainframe-mcp`
- Install: `/plugin install red-pill` (see README for details)

## Privacy
Everything local: embedding model, vector DB, MCP servers. No data leaves the machine.
