# Red Pill

Multi-tier research orchestrator + semantic knowledge base for Claude Code.

The Oracle sends cheap Haiku scouts in parallel, Sonnet synthesizes, Opus judges. The Mainframe stores and retrieves knowledge on demand. Take the red pill — see your codebase clearly.

## Install

```
/plugin install red-pill
```

That's it. The plugin registers MCP servers, installs dependencies, and creates directories automatically on first session.

## Quick Start

```
/red-pill                              # Initialize a project (scan, generate CLAUDE.md, health check)
/oracle what are the best testing frameworks for Swift   # Research anything
/mainframe save                        # Save knowledge for later
/mainframe search testing patterns     # Find stored knowledge
```

## Components

| Command | What it does |
|---|---|
| `/oracle [N] <question>` | N chains of 10 Haiku scouts + Sonnet synthesis. Default 1 chain. |
| `/mainframe save` | Save knowledge to the semantic knowledge base |
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
  Report auto-saved to Mainframe (searchable in future sessions)
```

## Prerequisites

- [Claude Code](https://claude.ai/code) with active subscription
- Node.js 18+ (for MCP servers)
- Python 3.10+ (for Oracle SDK)

## How the Mainframe Works

The Mainframe is a folder of markdown files at `~/.claude/mainframe/` with semantic search powered by [mcp-local-rag](https://github.com/shinpr/mcp-local-rag). Everything is local — no data leaves your machine.

```
~/.claude/mainframe/
├── library/        Reference material — conventions, gotchas, designs
└── oracle/         Auto-saved Oracle research reports
```

Search scores: < 0.3 strong match, 0.3-0.5 moderate, > 0.7 skip.

## Privacy

Everything runs locally:
- Embedding model downloads once (~90MB), runs on your machine
- Vector database stored on your disk
- MCP server is a local stdio process, no network listeners
- Your knowledge never leaves your machine

## License

MIT
