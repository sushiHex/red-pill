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
Multi-tier research orchestrator. Engine: `oracle_sdk.py`. Default 1 chain = 10 Smiths + 1 Anderson. Scaling: `/oracle 4` = 40 Smiths + 4 Andersons. Cost: 10 Haiku Smiths ≈ 0.17 Opus-equivalents.

### Mainframe (`/mainframe save | search`)
Local semantic knowledge base at `~/.claude/mainframe/`. Markdown files indexed by mcp-local-rag. Two categories: `library/` (reference) and `oracle/` (auto-saved reports). Search scores: < 0.3 strong, > 0.7 skip.

### Red Pill (`/red-pill`)
Project initialization. Scans codebase, searches Mainframe for conventions, generates/audits CLAUDE.md. Also: `/red-pill status` for health checks.

### Standalone Agents
- agent-smith (Opus) — deep multi-round research
- agent-jones (Sonnet) — standard queries
- agent-brown (Haiku) — quick lookups

## Key Constraints
- Three copies of oracle_sdk.py must stay in sync (skills, plugin, pip package)
- HTTP MCP broken in SDK v0.1.48 — stdio only
- Built-in subagents can't access MCP — use `gh` CLI via Bash
- Anderson stagger: 3s base + 2s per agent (multi-chain only) prevents subprocess race condition
- Smith prompts: ONE narrow question, under 150 words, multiple of 10

## Distribution
- Plugin: `github.com/sushiHex/red-pill` (private)
- Pip package: `github.com/sushiHex/claude-oracle` (private)
- Install: `/plugin marketplace add sushiHex/red-pill` then `/plugin install red-pill`

## Privacy
Everything local: embedding model, vector DB, MCP servers. No data leaves the machine.
