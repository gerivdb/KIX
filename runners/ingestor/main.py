#!/usr/bin/env python3
"""ingestor runner - BaseRunner (Phase 3)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from kix.libs.shared_clients.base_runner import BaseRunner


class IngestorRunner(BaseRunner):
    """Runner KIX pour ingestor."""

    def __init__(self, config_path: Path | None = None) -> None:
        super().__init__(name="ingestor", runner_type="python", port=0, config_path=config_path)

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute le runner ingestor (placeholder)."""
        return {"status": "ok", "runner": "ingestor"}


def main() -> int:
    runner = IngestorRunner()
    runner.start()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
