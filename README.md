# Red Pill

Multi-tier research orchestrator + semantic knowledge base for Claude Code.

The Oracle sends cheap Haiku scouts in parallel, Sonnet synthesizes, Opus judges. The Mainframe indexes all project knowledge for cross-project semantic search. Take the red pill — see your codebase clearly.

## Install

```
/plugin install red-pill
```

That's it. The plugin registers MCP servers, installs dependencies, and creates directories automatically on first session.

## Quick Start

```
/red-pill                              # Initialize a project (scan, generate CLAUDE.md, health check)
/oracle what are the best testing frameworks for Swift   # Research anything
/mainframe search testing patterns     # Find stored knowledge across all projects
```

## Components

| Command | What it does |
|---|---|
| `/oracle [N] <question>` | N chains of 10 Haiku scouts + Sonnet synthesis. Default 1 chain. |
| `/mainframe search <query>` | Semantic search across all project research, docs, and CLAUDE.md |
| `/mainframe save` | Save knowledge to the current project's research/ or docs/ directory |
| `/red-pill` | Initialize a project for the ecosystem |
| `/red-pill status` | System health check |
| `/red-pill audit` | Audit existing CLAUDE.md |

## Agents

Three standalone research agents, usable directly via the Agent tool:

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
  N*10 Haiku Smiths search in parallel (WebSearch, GitHub MCP, Read, Grep)
        |
  N Sonnet Andersons organize findings (one per chain, isolated)
        |
  Opus synthesizes the final answer
        |
  Report saved to project research/ (auto-ingested into Mainframe)
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

Default MCP backend: [mcp-local-rag](https://github.com/shinpr/mcp-local-rag) (CPU, ~90MB model). For GPU acceleration, see [mainframe-mcp](https://github.com/sushiHex/mainframe-mcp).

## Project File Placement

Every project follows this convention:
- `research/` — Oracle reports, API discoveries, analysis, findings
- `docs/` — Architecture, design decisions, API references, specs
- `CLAUDE.md` — Project conventions and gotchas
- No loose .md files in the project root

## Prerequisites

- [Claude Code](https://claude.ai/code) with active subscription
- Node.js 18+ (for MCP servers)
- Python 3.10+ (for Oracle SDK)

## Privacy

Everything runs locally:
- Embedding model downloads once, runs on your machine
- Vector database stored on your disk
- MCP server is a local stdio process, no network listeners
- Your knowledge never leaves your machine

## License

MIT
