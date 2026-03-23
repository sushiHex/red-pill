---
name: mainframe
description: "Save and search knowledge in the Mainframe — ~/.claude/mainframe/ indexed by mcp-local-rag for semantic search."
argument-hint: "save <description> | search <query>"
user-invocable: true
---

# /mainframe

## /mainframe save <content description>

1. Pick folder: `library/` (reference material) or `oracle/` (research reports)
2. Filename: `<topic-slug>.md` (lowercase, hyphens). For `oracle/` reports: `<YYYY-MM-DD>-<topic-slug>.md`.
3. Write plain markdown. H1 = topic name. One topic per file, under 500 lines.
4. If the same topic exists, update it — don't create duplicates.
5. Ingest via local-rag MCP `ingest_file`.

## /mainframe search <query>

1. Call local-rag MCP `query_documents` with the query.
2. Scores: < 0.3 strong, 0.3-0.5 moderate, > 0.7 skip.
3. Present: source file, score, key excerpt.
4. If no strong matches, suggest alternative search terms.

If the index needs rebuilding, run `npx -y mcp-local-rag` with `--db-path`, `--cache-dir`, and `--base-dir` all pointing to the user's `~/.claude/mainframe/` directory.
