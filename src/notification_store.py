"""Persistent notification history store (SQLite)."""

from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator, Optional


@dataclass
class NotificationRecord:
    id: int
    event: str
    timestamp: str
    phi_cps: float
    threshold: float
    consecutive_cycles: int
    service: Optional[str]
    channel: str
    payload: str


class NotificationStore:
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
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    phi_cps REAL NOT NULL,
                    threshold REAL NOT NULL,
                    consecutive_cycles INTEGER NOT NULL,
                    service TEXT,
                    channel TEXT NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_notifications_timestamp
                ON notifications (timestamp DESC)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_notifications_service
                ON notifications (service)
                """
            )

    def insert(self, event: str, timestamp: str, phi_cps: float, threshold: float, consecutive_cycles: int, service: Optional[str], channel: str, payload: dict[str, Any]) -> int:
        with self.transaction() as conn:
            cursor = conn.execute(
                """
                INSERT INTO notifications (event, timestamp, phi_cps, threshold, consecutive_cycles, service, channel, payload)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (event, timestamp, phi_cps, threshold, consecutive_cycles, service, channel, json.dumps(payload)),
            )
            return cursor.lastrowid

    def list_recent(self, limit: int = 100, service: Optional[str] = None) -> list[NotificationRecord]:
        query = "SELECT id, event, timestamp, phi_cps, threshold, consecutive_cycles, service, channel, payload FROM notifications"
        params = []
        if service:
            query += " WHERE service = ?"
            params.append(service)
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        with self.transaction() as conn:
            rows = conn.execute(query, params).fetchall()
        return [
            NotificationRecord(
                id=row["id"],
                event=row["event"],
                timestamp=row["timestamp"],
                phi_cps=row["phi_cps"],
                threshold=row["threshold"],
                consecutive_cycles=row["consecutive_cycles"],
                service=row["service"],
                channel=row["channel"],
                payload=row["payload"],
            )
            for row in rows
        ]
