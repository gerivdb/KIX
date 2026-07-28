"""Persistent notification metrics store (SQLite)."""

from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator, Optional


@dataclass
class NotificationMetrics:
    channel: str
    total_sent: int = 0
    total_success: int = 0
    total_failed: int = 0
    avg_latency_ms: float = 0.0
    last_sent_at: Optional[str] = None


class NotificationMetricsStore:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_schema()

    def _conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Connection, None, None]:
        conn = self._conn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def _init_schema(self) -> None:
        with self.transaction() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS notification_metrics (
                    channel TEXT PRIMARY KEY,
                    total_sent INTEGER NOT NULL DEFAULT 0,
                    total_success INTEGER NOT NULL DEFAULT 0,
                    total_failed INTEGER NOT NULL DEFAULT 0,
                    avg_latency_ms REAL NOT NULL DEFAULT 0.0,
                    last_sent_at TEXT
                )
                """
            )

    def record_send(self, channel: str, success: bool, latency_ms: float) -> None:
        with self.transaction() as conn:
            row = conn.execute(
                "SELECT total_sent, total_success, total_failed, avg_latency_ms FROM notification_metrics WHERE channel = ?",
                (channel,),
            ).fetchone()
            if row:
                total_sent = row["total_sent"] + 1
                total_success = row["total_success"] + (1 if success else 0)
                total_failed = row["total_failed"] + (0 if success else 1)
                avg_latency_ms = ((row["avg_latency_ms"] * row["total_sent"]) + latency_ms) / total_sent
                conn.execute(
                    """
                    UPDATE notification_metrics
                    SET total_sent = ?, total_success = ?, total_failed = ?, avg_latency_ms = ?, last_sent_at = ?
                    WHERE channel = ?
                    """,
                    (total_sent, total_success, total_failed, avg_latency_ms, datetime.now(timezone.utc).isoformat(), channel),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO notification_metrics (channel, total_sent, total_success, total_failed, avg_latency_ms, last_sent_at)
                    VALUES (?, 1, ?, ?, ?, ?)
                    """,
                    (channel, 1 if success else 0, 0 if success else 1, latency_ms, datetime.now(timezone.utc).isoformat()),
                )

    def list_all(self) -> dict[str, NotificationMetrics]:
        with self.transaction() as conn:
            rows = conn.execute("SELECT channel, total_sent, total_success, total_failed, avg_latency_ms, last_sent_at FROM notification_metrics").fetchall()
        return {
            row["channel"]: NotificationMetrics(
                channel=row["channel"],
                total_sent=row["total_sent"],
                total_success=row["total_success"],
                total_failed=row["total_failed"],
                avg_latency_ms=row["avg_latency_ms"],
                last_sent_at=row["last_sent_at"],
            )
            for row in rows
        }
