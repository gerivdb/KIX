"""Auto-remediation store and engine for KIX."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


@dataclass
class RemediationResult:
    policy_id: str
    service: Optional[str]
    action_type: str
    success: bool
    detail: str
    timestamp: str


class RemediationStore:
    """Persistent store for remediation actions and results."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _init_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS remediation_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    policy_id TEXT NOT NULL,
                    service TEXT,
                    action_type TEXT NOT NULL,
                    success INTEGER NOT NULL,
                    detail TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_remediation_timestamp
                ON remediation_actions (timestamp DESC)
                """
            )

    def record(self, result: RemediationResult) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO remediation_actions (policy_id, service, action_type, success, detail, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (result.policy_id, result.service, result.action_type, 1 if result.success else 0, result.detail, result.timestamp),
            )
            return cursor.lastrowid

    def list_recent(self, limit: int = 100) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT policy_id, service, action_type, success, detail, timestamp FROM remediation_actions ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]
