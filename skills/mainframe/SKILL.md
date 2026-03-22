---
name: mainframe
description: "The Mainframe — persistent knowledge base for the Oracle system. Save, search, rebuild, and maintain the semantic knowledge store at ~/.claude/mainframe/."
argument-hint: "[save|rebuild|clean]"
user-invocable: true
---

# /mainframe — The Mainframe

The Oracle researches. The Mainframe remembers. Markdown files at `~/.claude/mainframe/` indexed by mcp-local-rag for semantic search.

## /mainframe save <content description>

1. Pick category: `library/` `oracle/` `architecture/` `gotchas/` `research/` `notes/`
2. Filename: `<topic-slug>.md` (lowercase, hyphens, dates only for oracle/)
3. Write with YAML frontmatter: title, tags, created, updated
4. Ingest via local-rag MCP `ingest_file`
5. If same topic exists, update it — don't create duplicates
6. One topic per file. Under 500 lines. Split if larger.

## /mainframe rebuild

```bash
npx -y mcp-local-rag --db-path ~/.claude/mainframe/.lancedb --cache-dir ~/.claude/mainframe/.models ingest --base-dir ~/.claude/mainframe ~/.claude/mainframe
```

Note: On Windows, if `~` doesn't expand, use the full path (e.g., `C:/Users/<username>/.claude/mainframe`).

## /mainframe clean

1. Find .md files missing YAML frontmatter → add it
2. Files over 500 lines → suggest splitting
3. `updated` older than 6 months → flag as stale
4. Unindexed files → ingest them
5. Fix what's fixable, report what needs manual attention

## Auto-save convention

When saving to the Mainframe from any skill: write file with frontmatter, then call `ingest_file`.
