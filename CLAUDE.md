# Red Pill — Claude Code Plugin

Multi-tier research orchestrator + semantic knowledge base.

## Stack
- Python 3.10+, claude_agent_sdk, Node.js (npx for MCP)
- Plugin format: `.claude-plugin/plugin.json`

## Structure
```
.claude-plugin/plugin.json   ← Plugin manifest
.mcp.json                    ← Registers local-rag MCP server
hooks/hooks.json             ← SessionStart: pip install + mkdir
agents/                      ← agent-smith, agent-jones, agent-brown
skills/
  oracle/                    ← /oracle command + oracle_sdk.py engine
  mainframe/                 ← /mainframe save|rebuild|clean
  red-pill/                  ← /red-pill project initialization
```

## Conventions
- Plugin names are kebab-case
- Skills reference Mainframe at `~/.claude/mainframe/`, not hardcoded user paths
- `.mcp.json` uses `${HOME}` for cross-platform paths
- Oracle SKILL.md tells Claude to find oracle_sdk.py adjacent to the SKILL.md file

## Gotchas
- `cmd /c npx` needed on some Windows setups — `.mcp.json` uses bare `npx` (works in Git Bash)
- No postInstall hooks in plugin system — use SessionStart hook instead
- `${CLAUDE_PLUGIN_ROOT}` not available in SKILL.md text — only in hooks and .mcp.json
