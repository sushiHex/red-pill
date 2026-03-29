---
name: mainframe
description: "Search and manage the Mainframe knowledge base — all project research/, docs/, and CLAUDE.md indexed by mainframe-mcp (GPU)."
argument-hint: "search <query> | save <description>"
user-invocable: true
---

# /mainframe

## /mainframe search <query>

1. Call mainframe MCP `search` with the query.
2. Results are reranked by cross-encoder. Lower score = more relevant.
3. Present: source file, project, score, key excerpt.
4. If no strong matches, suggest alternative search terms.

## /mainframe save <content description>

Save to the current project's `research/` or `docs/` directory (not the Mainframe directly).
The scanner auto-ingests project files into the Mainframe index.

1. Determine if content is research (discoveries, analysis) or docs (architecture, specs).
2. Write to `research/<topic-slug>.md` or `docs/<topic-slug>.md`.
3. File will be auto-ingested on next `ingest_projects` call.
