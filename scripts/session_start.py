"""SessionStart hook: install Oracle + Mainframe, seed first-run config.

Runs once per Claude Code session start (see hooks/hooks.json). Every step is
a no-op if its precondition is already satisfied, so it's safe to run every
session. Never raises -- a hook failure must not block session startup.
"""
from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

# import name -> pip install spec. Neither package is on PyPI.
DEPENDENCIES = {
    "claude_oracle": "git+https://github.com/sushiHex/claude-oracle.git",
    "mainframe_mcp": "git+https://github.com/sushiHex/mainframe-mcp.git",
}

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
MAINFRAME_DIR = Path.home() / ".claude" / "mainframe"


def _ensure_installed(import_name: str, pip_spec: str) -> None:
    if importlib.util.find_spec(import_name) is not None:
        return
    subprocess.run(
        [sys.executable, "-m", "pip", "install", pip_spec],
        capture_output=True,
        check=False,
    )


def _seed_config() -> None:
    MAINFRAME_DIR.mkdir(parents=True, exist_ok=True)
    config_path = MAINFRAME_DIR / "config.json"
    if config_path.exists():
        return
    preset = PLUGIN_ROOT / "configs" / "cpu-only.json"
    if preset.exists():
        shutil.copy(preset, config_path)


def main() -> None:
    for import_name, pip_spec in DEPENDENCIES.items():
        _ensure_installed(import_name, pip_spec)
    _seed_config()


if __name__ == "__main__":
    try:
        main()
    except Exception:  # a hook failure must never block session startup
        pass
