"""Audit log store for KIX."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


class AuditLogStore:
    """Persistent store for audit log entries."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _init_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    method TEXT NOT NULL,
                    username TEXT,
                    timestamp TEXT NOT NULL,
                    details TEXT,
                    ip_address TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_audit_timestamp
                ON audit_log (timestamp DESC)
                """
            )

    def record(
        self,
        action: str,
        endpoint: str,
        method: str,
        username: Optional[str],
        details: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO audit_log (action, endpoint, method, username, timestamp, details, ip_address)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    action,
                    endpoint,
                    method,
                    username,
                    datetime.now(timezone.utc).isoformat(),
                    details,
                    ip_address,
                ),
            )
            return cursor.lastrowid

    def list_recent(self, limit: int = 100) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT id, action, endpoint, method, username, timestamp, details, ip_address
                FROM audit_log
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]
