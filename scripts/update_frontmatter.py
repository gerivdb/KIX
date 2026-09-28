#!/usr/bin/env python3
"""Update frontmatter in all PRD-MOC files."""

from __future__ import annotations

import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PRD_MOC_DIR = BASE_DIR / "PRD-MOC"
TODAY = datetime.now(timezone(timedelta(hours=2))).strftime("%Y-%m-%d")


def update_frontmatter(path: Path) -> None:
    content = path.read_text(encoding="utf-8")
    updated = re.sub(
        r"^(updated:)\s*['\"]?\d{4}-\d{2}-\d{2}['\"]?",
        f"\\1 \"{TODAY}\"",
        content,
        count=1,
        flags=re.MULTILINE,
    )
    if content != updated:
        path.write_text(updated, encoding="utf-8")
        print(f"Updated frontmatter: {path.name}")
    else:
        print(f"No change: {path.name}")


def main() -> int:
    for md in sorted(PRD_MOC_DIR.glob("*.md")):
        update_frontmatter(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
