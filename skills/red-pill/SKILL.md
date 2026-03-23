---
name: red-pill
description: "Initialize or audit a project's CLAUDE.md. Scans codebase, searches Mainframe for relevant knowledge, applies Boris Cherny's principles."
argument-hint: "[audit|status|global]"
user-invocable: true
---

# /red-pill — Project Initialization

## Parse Arguments

- `/red-pill` — If CLAUDE.md exists, audit it. Otherwise generate one.
- `/red-pill audit` — Audit existing CLAUDE.md
- `/red-pill global` — Audit `~/.claude/CLAUDE.md`
- `/red-pill status` — System health check (Node.js, SDK, MCP, Mainframe)

## Generate (no existing CLAUDE.md)

1. Read project structure: `ls`, `package.json`, `pyproject.toml`, etc.
2. Identify: language, framework, test runner, build tool
3. Search the Mainframe for relevant conventions and gotchas for this stack
4. Generate a CLAUDE.md:
   - Under 60 lines. Only rules that prevent mistakes.
   - Sections: Stack, Structure, Commands, Conventions, Gotchas
   - Exact commands, not descriptions
   - Only rules that differ from Claude's defaults

## Audit (CLAUDE.md exists)

1. Read it. Count lines — flag if over 200.
2. Each line: "Would removing this cause Claude to make mistakes?" If not, cut it.
3. Search Mainframe for known gotchas for this stack — flag any missing.
4. Report: keep / cut / add.

## Status

1. `node --version` — Node.js present?
2. `pip show claude-agent-sdk` — SDK installed?
3. Call `list_files` via local-rag MCP — responding?
4. Report what's ready, what's missing.
