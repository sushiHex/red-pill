---
name: red-pill
description: "Initialize a project for The Matrix ecosystem. Scans codebase, searches Mainframe for relevant knowledge, generates CLAUDE.md, verifies system health."
argument-hint: "[audit|status]"
user-invocable: true
---

# /red-pill — Project Initialization

Take the red pill. See your project clearly.

## Parse Arguments

- `/red-pill` — Full setup: generate/audit CLAUDE.md + system health check
- `/red-pill audit` — Just audit existing CLAUDE.md against Mainframe knowledge
- `/red-pill status` — Just check system health

## Full Setup (default)

### Step 1: System Health Check
1. Check Node.js: `node --version` (required for MCP)
2. Check claude-agent-sdk: `python -c "import claude_agent_sdk; print(claude_agent_sdk.__version__)"` — if missing, run `pip install claude-agent-sdk>=0.1.48`
3. Check Mainframe directories exist at `~/.claude/mainframe/` — if missing, create them
4. Check local-rag MCP is responding: call `list_files` via the MCP server
5. Check global CLAUDE.md has Mainframe section — if missing, append it:
   ```
   ## Mainframe
   - Knowledge base at `~/.claude/mainframe/` indexed by mcp-local-rag. Use `/mainframe save` to add content.
   - Save research, reports, and reusable knowledge to the Mainframe — not to project directories.
   - Search scores: < 0.3 strong, 0.3-0.5 moderate, > 0.7 skip.
   - If the Mainframe doesn't have what you need, research the answer, then `/mainframe save` the findings.
   ```
6. Report: what's ready, what was fixed, what needs manual attention

### Step 2: CLAUDE.md Generation/Audit

If no CLAUDE.md exists in the current project:
1. Read the project structure: `ls`, `package.json`, `pyproject.toml`, `Cargo.toml`, etc.
2. Identify: language, framework, test runner, build tool, package manager
3. Search the Mainframe for relevant conventions and gotchas for this stack
4. Generate a CLAUDE.md following Boris Cherny's principles:
   - Under 200 lines. Only rules that prevent mistakes.
   - WHAT (stack/structure) / WHY (purpose) / HOW (commands/conventions)
   - Gotchas section for non-obvious behavior
   - Exact commands, not descriptions
   - Divergence-only conventions (skip what Claude already knows)

If CLAUDE.md already exists:
1. Read it and count lines (flag if over 200)
2. Check each line: "Would removing this cause Claude to make mistakes?"
3. Search the Mainframe for known gotchas related to this stack — flag any missing
4. Report: lines that earn their tokens (keep), token waste (cut), missing content (add)

### Step 3: Summary
Report the full status:
```
System:  [ready/issues]
CLAUDE.md: [generated/audited/N lines]
Mainframe: [N files indexed]
Oracle:  [ready/missing SDK]
```

## Status Check Only

Run Step 1 only. Quick health check without touching CLAUDE.md.
