"""Tests for notification_store."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

from src.notification_store import NotificationRecord, NotificationStore


def test_insert_and_list(tmp_path: Path) -> None:
    db = tmp_path / "notifications.db"
    store = NotificationStore(db)
    store.insert(
        event="phi_cps_degraded",
        timestamp="2026-07-28T04:00:00+00:00",
        phi_cps=0.7,
        threshold=0.9,
        consecutive_cycles=3,
        service="RLM-GRAPH",
        channel="webhook",
        payload={"items": []},
    )
    records = store.list_recent(limit=10)
    assert len(records) == 1
    r = records[0]
    assert r.event == "phi_cps_degraded"
    assert r.phi_cps == 0.7
    assert r.channel == "webhook"
    assert r.service == "RLM-GRAPH"


def test_list_filters_by_service(tmp_path: Path) -> None:
    db = tmp_path / "notifications.db"
    store = NotificationStore(db)
    store.insert(
        event="phi_cps_degraded",
        timestamp="2026-07-28T04:00:00+00:00",
        phi_cps=0.7,
        threshold=0.9,
        consecutive_cycles=3,
        service="RLM-GRAPH",
        channel="webhook",
        payload={},
    )
    store.insert(
        event="phi_cps_degraded",
        timestamp="2026-07-28T04:01:00+00:00",
        phi_cps=0.6,
        threshold=0.9,
        consecutive_cycles=3,
        service="RLM-CONFIG",
        channel="email",
        payload={},
    )
    records = store.list_recent(limit=10, service="RLM-GRAPH")
    assert len(records) == 1
    assert records[0].service == "RLM-GRAPH"


def test_list_respects_limit(tmp_path: Path) -> None:
    db = tmp_path / "notifications.db"
    store = NotificationStore(db)
    for i in range(10):
        store.insert(
            event="phi_cps_degraded",
            timestamp=f"2026-07-28T04:{i:02d}:00+00:00",
            phi_cps=0.5,
            threshold=0.9,
            consecutive_cycles=3,
            service="RLM-GRAPH",
            channel="webhook",
            payload={},
        )
    records = store.list_recent(limit=5)
    assert len(records) == 5
    assert records[0].timestamp == "2026-07-28T04:09:00+00:00"
    assert records[-1].timestamp == "2026-07-28T04:05:00+00:00"


def test_schema_created_once(tmp_path: Path) -> None:
    db = tmp_path / "notifications.db"
    store1 = NotificationStore(db)
    store2 = NotificationStore(db)
    store1.insert(
        event="phi_cps_degraded",
        timestamp="2026-07-28T04:00:00+00:00",
        phi_cps=0.7,
        threshold=0.9,
        consecutive_cycles=3,
        service="RLM-GRAPH",
        channel="webhook",
        payload={},
    )
    records = store2.list_recent(limit=10)
    assert len(records) == 1
