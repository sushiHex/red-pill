# Red Pill

**Agentic research toolkit for Claude Code.** Dispatch a single read-only agent for a quick lookup, or launch a coordinated multi-agent fleet for deep investigation — everything draws on a persistent semantic memory that recalls what you've already found. Take the red pill — see your codebase clearly.

## Install

```
/plugin install red-pill
```

That's it. The plugin registers the MCP server, installs dependencies, and creates directories automatically on first session.

## Agents

Three standalone, read-only research agents — dispatch one directly via the Agent tool for a single question, no orchestration needed:

| Agent | Model | Use for |
|---|---|---|
| agent-smith | Opus | Deep research, multi-round investigation |
| agent-jones | Sonnet | Standard codebase queries, moderate-depth research |
| agent-brown | Haiku | Quick lookups, simple searches, fast fact-checking |

All three investigate and report — they never create, modify, delete, or install anything, even if asked to.

## Oracle — multi-agent research fleets

When one agent's pass isn't enough coverage, `/oracle` coordinates a full fleet instead of a single dispatch:

```
/oracle what are the best testing frameworks for Swift
/oracle 4 <question>     # 4 chains = 40 Haiku scouts + 4 Sonnet synthesizers, isolated per chain
```

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

Same guarantee as the standalone agents: pure investigation, no side effects. Provided by the independent [claude-oracle](https://github.com/sushiHex/claude-oracle) project — Red Pill installs it as a dependency rather than bundling a fork.

## Mainframe — memory for every agent above

Every agent and fleet above can draw on a semantic index of everything you've already researched, across every project. It's ambient: no slash command, it loads itself into context whenever a task would benefit from recalling prior work.

```
~/repos/project-a/research/*.md  ──→ indexed
~/repos/project-a/docs/*.md      ──→ indexed
~/repos/project-a/CLAUDE.md      ──→ indexed
~/repos/project-b/research/*.md  ──→ indexed
...all searchable from any project, by any agent
```

Backend: [mainframe-mcp](https://github.com/sushiHex/mainframe-mcp). Red Pill
seeds its bundled `configs/cpu-only.json` (`BAAI/bge-small-en-v1.5`, no GPU
required) to `~/.claude/mainframe/config.json` on first run, so it works out
of the box. For GPU-accelerated models (larger embedders, rerankers, and an
LLM consolidator), replace that file's contents with one of the presets in
[mainframe-mcp's own `configs/`](https://github.com/sushiHex/mainframe-mcp/tree/main/configs)
(not installed by pip — copy the preset you want). `mainframe-mcp`'s own
dependencies (`bitsandbytes`, `accelerate`, `sentence-transformers`, …) install
regardless of which config you run, so first install is heavier than a
CPU-only backend would otherwise be.

## Project Init

`/red-pill` generates or audits a project's `CLAUDE.md`, searching the Mainframe for relevant conventions and gotchas along the way. `/red-pill status` checks that Oracle and Mainframe are installed and responding.

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
