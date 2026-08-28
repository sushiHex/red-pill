# Red Pill

Multi-tier research orchestrator + semantic knowledge base for Claude Code.

The Oracle sends cheap Haiku scouts in parallel, Sonnet synthesizes, Opus judges. The Mainframe indexes all project knowledge for cross-project semantic search. Take the red pill — see your codebase clearly.

## Install

```
/plugin install red-pill
```

That's it. The plugin registers the MCP server, installs dependencies, and creates directories automatically on first session.

## Quick Start

```
/red-pill                              # Initialize or audit a project's CLAUDE.md
/oracle what are the best testing frameworks for Swift   # Research anything
```

The Mainframe has no slash command — it's an ambient skill that loads itself
whenever a task would benefit from recalling prior research (see below).

## Components

| Command | What it does |
|---|---|
| `/oracle [N] <question>` | N chains of 10 Haiku scouts + Sonnet synthesis. Default 1 chain. |
| `/red-pill` | Initialize a project for the ecosystem |
| `/red-pill status` | System health check |
| `/red-pill audit` | Audit existing CLAUDE.md |

Oracle and Mainframe are provided by their own independent, standalone projects
([claude-oracle](https://github.com/sushiHex/claude-oracle),
[mainframe-mcp](https://github.com/sushiHex/mainframe-mcp)) — Red Pill installs
them as dependencies and wires them into Claude Code rather than bundling its
own forks.

## Agents

Three standalone read-only research agents, usable directly via the Agent tool.
They investigate and report — they never create, modify, or delete files:

| Agent | Model | Use for |
|---|---|---|
| agent-smith | Opus | Deep research, multi-round investigation |
| agent-jones | Sonnet | Standard codebase queries, moderate-depth research |
| agent-brown | Haiku | Quick lookups, simple searches, fast fact-checking |

## Architecture

```
You ask a question
        |
   /oracle [N]
        |
  Opus decomposes into N*10 focused prompts
        |
  N*10 Haiku Smiths search in parallel (WebSearch, WebFetch by default;
  add --local for Read/Grep/Glob, or set GITHUB_PAT for GitHub MCP)
        |
  N Sonnet Andersons organize findings (one per chain, isolated)
        |
  Opus synthesizes the final answer
        |
  Optionally saved to project research/ (auto-ingested into Mainframe on next sync)
```

## How the Mainframe Works

The Mainframe indexes all project `research/`, `docs/`, and `CLAUDE.md` files for cross-project semantic search. Knowledge lives in your projects — the Mainframe just makes it searchable from anywhere.

```
~/repos/project-a/research/*.md  ──→ indexed
~/repos/project-a/docs/*.md      ──→ indexed
~/repos/project-a/CLAUDE.md      ──→ indexed
~/repos/project-b/research/*.md  ──→ indexed
...all searchable from any project
```

Backend: [mainframe-mcp](https://github.com/sushiHex/mainframe-mcp). Red Pill
seeds its bundled `configs/cpu-only.json` (`BAAI/bge-small-en-v1.5`, no GPU
required) to `~/.claude/mainframe/config.json` on first run, so it works out
of the box. For GPU-accelerated models (larger embedders, rerankers, and an
LLM consolidator), replace that file's contents with one of the presets in
[mainframe-mcp's own `configs/`](https://github.com/sushiHex/mainframe-mcp/tree/main/configs)
(not installed by pip — copy the preset you want). `mainframe-mcp`'s own
dependencies (`bitsandbytes`, `accelerate`, `sentence-transformers`, …) install
regardless of which config you run, so first install is heavier than Red
Pill's previous CPU-only backend.

## Project File Placement

Every project follows this convention:
- `research/` — Oracle reports, API discoveries, analysis, findings
- `docs/` — Architecture, design decisions, API references, specs
- `CLAUDE.md` — Project conventions and gotchas
- No loose .md files in the project root

## Prerequisites

- [Claude Code](https://claude.ai/code) with active subscription
- `git` (both Oracle and Mainframe install from GitHub — neither is on PyPI)
- Python 3.10+ (runs both Oracle and Mainframe)
- Node.js 18+ — optional, only needed if you set `GITHUB_PAT` for Oracle's
  GitHub MCP scouting

## Privacy

Everything runs locally:
- Embedding model downloads once, runs on your machine
- Vector database stored on your disk
- MCP server is a local stdio process, no network listeners
- Your knowledge never leaves your machine

## License

MIT
