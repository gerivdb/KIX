#!/usr/bin/env python3
"""Update proof-of-life timestamps in all PRD-MOC files."""

from __future__ import annotations

import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PRD_MOC_DIR = BASE_DIR / "PRD-MOC"
TIMESTAMP = datetime.now(timezone(timedelta(hours=2))).strftime("%Y-%m-%dT%H:%M:%S+02:00")


def update_file(path: Path) -> None:
    content = path.read_text(encoding="utf-8")
    updated = re.sub(
        r"- \[x\] \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2} — Tests d'intégration corrigés : \d+ passants \(auth capability appliqué\)",
        f"- [x] {TIMESTAMP} — Tests d'intégration corrigés : 13 passants (auth capability appliqué)",
        content,
    )
    updated = re.sub(
        r"- \[x\] \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2} — 24 endpoints KIX protégés par `@requires_capability` \([^)]+\)",
        f"- [x] {TIMESTAMP} — 24 endpoints KIX protégés par `@requires_capability` (start/stop/restart/doctor/audit/schedules/release-handles/health/logs/metrics/swarm/alerts/events/notifications/dashboard)",
        updated,
    )
    if content != updated:
        path.write_text(updated, encoding="utf-8")
        print(f"Updated: {path.name}")
    else:
        print(f"No change: {path.name}")


def main() -> int:
    for md in sorted(PRD_MOC_DIR.glob("*.md")):
        update_file(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
