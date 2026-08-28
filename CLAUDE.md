# Red Pill — Claude Code Plugin

Multi-tier research orchestrator + semantic knowledge base.

## Stack
- Python 3.10+, Node.js (for `gh`/misc — no MCP server is npx-based anymore)
- Plugin format: `.claude-plugin/plugin.json`
- Oracle and Mainframe are external dependencies (`claude-oracle`, `mainframe-mcp`
  — both on GitHub only, not PyPI), not vendored code. See docs/red-pill-system-overview.md.

## Structure
```
.claude-plugin/plugin.json   ← Plugin manifest
.mcp.json                    ← Registers mainframe-mcp (python -m mainframe_mcp.server)
configs/cpu-only.json        ← Seeded to ~/.claude/mainframe/config.json on first run
hooks/hooks.json             ← SessionStart: pip install claude-oracle + mainframe-mcp, mkdir, seed config
agents/                      ← agent-smith, agent-jones, agent-brown
skills/
  oracle/                    ← unmodified copy of claude-oracle's own SKILL.md
  mainframe-retrieval/       ← unmodified copy of mainframe-mcp's own SKILL.md (ambient, no slash command)
  red-pill/                  ← /red-pill project initialization
```

## Conventions
- Plugin names are kebab-case
- Skills reference Mainframe at `~/.claude/mainframe/`, not hardcoded user paths
- `.mcp.json` uses `${HOME}` for cross-platform paths
- `skills/oracle/SKILL.md` and `skills/mainframe-retrieval/SKILL.md` are copies of
  those projects' own bundled skill docs — **never edit them here.** Fix upstream
  in `claude-oracle`/`mainframe-mcp`, then re-copy the file verbatim into this repo.

## Gotchas
- Neither `claude-oracle` nor `mainframe-mcp` is on PyPI — the SessionStart hook
  installs both via `pip install git+https://github.com/sushiHex/<repo>.git`,
  which needs `git` and network access at first-session time.
- `mainframe-mcp`'s core dependencies (`bitsandbytes`, `accelerate`,
  `sentence-transformers`, `lancedb`, `pylance`, `tantivy`) install unconditionally
  regardless of which config is selected — first install is much heavier than the
  old bundled `mcp-local-rag` backend was. `bitsandbytes` in particular can be
  finicky without a CUDA GPU; the seeded `configs/cpu-only.json` avoids needing
  one at *runtime*, but does not avoid installing it.
- No postInstall hooks in plugin system — use SessionStart hook instead
- `${CLAUDE_PLUGIN_ROOT}` not available in SKILL.md text — only in hooks and .mcp.json
