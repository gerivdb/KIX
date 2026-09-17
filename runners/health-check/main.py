#!/usr/bin/env python3
"""health-check runner - BaseRunner (Phase 3)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from kix.libs.shared_clients.base_runner import BaseRunner


class HealthCheckRunner(BaseRunner):
    """Runner KIX pour health-check."""

    def __init__(self, config_path: Path | None = None) -> None:
        super().__init__(name="health-check", runner_type="python", port=0, config_path=config_path)

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute le runner health-check (placeholder)."""
        return {"status": "ok", "runner": "health-check"}


def main() -> int:
    runner = HealthCheckRunner()
    runner.start()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
