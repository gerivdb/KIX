"""Persistent runner state store (SQLite)."""

from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator, Optional


@dataclass
class RunnerRecord:
    name: str
    status: str
    pid: Optional[int]
    started_at: Optional[str]
    updated_at: str


class RunnerStateStore:
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
                CREATE TABLE IF NOT EXISTS runners (
                    name TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    pid INTEGER,
                    started_at TEXT,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def upsert(self, name: str, status: str, pid: Optional[int], started_at: Optional[str], updated_at: str) -> None:
        with self.transaction() as conn:
            conn.execute(
                """
                INSERT INTO runners (name, status, pid, started_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    status=excluded.status,
                    pid=excluded.pid,
                    started_at=excluded.started_at,
                    updated_at=excluded.updated_at
                """,
                (name, status, pid, started_at, updated_at),
            )

    def list_all(self) -> dict[str, RunnerRecord]:
        with self.transaction() as conn:
            rows = conn.execute("SELECT name, status, pid, started_at, updated_at FROM runners").fetchall()
        return {
            row["name"]: RunnerRecord(
                name=row["name"],
                status=row["status"],
                pid=row["pid"],
                started_at=row["started_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        }

    def get(self, name: str) -> Optional[RunnerRecord]:
        with self.transaction() as conn:
            row = conn.execute("SELECT name, status, pid, started_at, updated_at FROM runners WHERE name = ?", (name,)).fetchone()
        if not row:
            return None
        return RunnerRecord(
            name=row["name"],
            status=row["status"],
            pid=row["pid"],
            started_at=row["started_at"],
            updated_at=row["updated_at"],
        )
