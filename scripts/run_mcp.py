#!/usr/bin/env python3
"""Start the final-review MCP server with the plugin-managed Python env."""

from __future__ import annotations

import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "scripts" / "final_review_mcp.py"


def venv_python() -> Path:
    if os.name == "nt":
        return ROOT / ".venv" / "Scripts" / "python.exe"
    return ROOT / ".venv" / "bin" / "python"


def main() -> None:
    managed_python = venv_python()
    executable = managed_python if managed_python.exists() else Path(sys.executable)
    os.execv(str(executable), [str(executable), str(SERVER)])


if __name__ == "__main__":
    main()
