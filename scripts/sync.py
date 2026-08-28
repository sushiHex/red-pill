"""DEV ONLY: copy plugin files into the local Claude Code installation.

Not for end users -- the plugin system handles installation automatically.
This overwrites files under ~/.claude/{skills,agents} without confirmation.

Usage: python scripts/sync.py
"""
from __future__ import annotations

import shutil
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
CLAUDE_DIR = Path.home() / ".claude"


def _sync_dir(src: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        target = dst / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        else:
            shutil.copy2(item, target)


def main() -> None:
    _sync_dir(PLUGIN_ROOT / "skills", CLAUDE_DIR / "skills")
    _sync_dir(PLUGIN_ROOT / "agents", CLAUDE_DIR / "agents")
    print(f"Synced plugin -> {CLAUDE_DIR}")


if __name__ == "__main__":
    main()
