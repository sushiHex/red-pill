"""DEV ONLY: copy plugin files into the local Claude Code installation.

Not for end users -- the plugin system handles installation automatically.
This overwrites files under ~/.claude/{skills,agents} without confirmation,
except one that is newer: a file whose first heading carries a higher version
(e.g. `# Oracle v4.9.0`, `# Agent Smith ... v1.13`) than the plugin's copy is
kept, so syncing a stale checkout can't silently downgrade a live install.

Usage: python scripts/sync.py
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
CLAUDE_DIR = Path.home() / ".claude"
_HEADING_VERSION = re.compile(r"^#\s.*?\bv(\d+(?:\.\d+)+)", re.MULTILINE)


def heading_version(path: Path) -> tuple[int, ...] | None:
    """The version in a markdown file's first heading, or None."""
    if path.suffix != ".md" or not path.is_file():
        return None
    match = _HEADING_VERSION.search(path.read_text(encoding="utf-8", errors="replace"))
    return tuple(int(part) for part in match[1].split(".")) if match else None


def _sync_file(src: Path, dst: Path) -> None:
    ours, theirs = heading_version(src), heading_version(dst)
    if ours and theirs and theirs > ours:
        print(f"kept newer {dst} (v{'.'.join(map(str, theirs))} > plugin v{'.'.join(map(str, ours))})")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _sync_dir(src: Path, dst: Path) -> None:
    for item in src.rglob("*"):
        if item.is_file():
            _sync_file(item, dst / item.relative_to(src))


def main() -> None:
    _sync_dir(PLUGIN_ROOT / "skills", CLAUDE_DIR / "skills")
    _sync_dir(PLUGIN_ROOT / "agents", CLAUDE_DIR / "agents")
    print(f"Synced plugin -> {CLAUDE_DIR}")


if __name__ == "__main__":
    main()
