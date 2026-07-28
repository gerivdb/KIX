"""Tests for KIX audit log store."""

import pytest
from pathlib import Path
from src.audit_log import AuditLogStore


@pytest.fixture
def audit_db(tmp_path: Path) -> str:
    return str(tmp_path / "audit.db")


def test_audit_log_record_and_list(audit_db: str) -> None:
    store = AuditLogStore(audit_db)
    store.record("runner_start", "/runners/RLM-GRAPH/start", "POST", "admin", details="started RLM-GRAPH", ip_address="127.0.0.1")
    store.record("runner_stop", "/runners/RLM-GRAPH/stop", "POST", "operator", details="stopped RLM-GRAPH", ip_address="127.0.0.1")
    items = store.list_recent(limit=10)
    assert len(items) == 2
    assert items[0]["action"] == "runner_stop"
    assert items[0]["username"] == "operator"
    assert items[0]["endpoint"] == "/runners/RLM-GRAPH/stop"
    assert items[1]["action"] == "runner_start"
    assert items[1]["username"] == "admin"


def test_audit_log_respects_limit(audit_db: str) -> None:
    store = AuditLogStore(audit_db)
    for i in range(5):
        store.record("action", "/endpoint", "GET", "admin", details=f"item {i}")
    items = store.list_recent(limit=2)
    assert len(items) == 2
    assert items[0]["details"] == "item 4"
    assert items[1]["details"] == "item 3"
