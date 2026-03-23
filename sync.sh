#!/bin/bash
# sync.sh — copy plugin files to local Claude Code installation
PLUGIN_DIR="$(cd "$(dirname "$0")" && pwd)"
cp -r "$PLUGIN_DIR/skills/"* "$HOME/.claude/skills/"
cp "$PLUGIN_DIR/agents/"* "$HOME/.claude/agents/"
echo "Synced plugin -> ~/.claude/"
