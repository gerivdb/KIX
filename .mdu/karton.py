#!/usr/bin/env python3
"""KIX - Central orchestrator for RLM runners."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], cwd: Path | None = None) -> int:
    print(f"[KIX] {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd)
    return result.returncode


def main() -> int:
    root = Path(__file__).resolve().parent
    venv = root / ".venv"
    python = venv / "Scripts" / "python.exe" if sys.platform == "win32" else venv / "bin" / "python"

    if not python.exists():
        print("[KIX] Missing .venv, falling back to system python")
        python = Path(sys.executable)

    commands = [
        [str(python), "-m", "pip", "install", "--quiet", "flask", "pyyaml"],
        [str(python), "-m", "pytest", "tests/", "-q"],
    ]

    status = 0
    for cmd in commands:
        code = run(cmd, cwd=root)
        if code != 0:
            status = code
            break

    return status


if __name__ == "__main__":
    raise SystemExit(main())
