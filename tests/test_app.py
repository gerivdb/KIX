"""Tests for KIX orchestrator."""

import os
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from flask import Flask
from src.runner_state import RunnerStateStore
from src.app import _load_known_repositories
from src.notification_store import NotificationRecord
from src.notification_metrics import NotificationMetrics
from src.auto_remediation import RemediationResult
from src.audit_log import AuditLogStore


@pytest.fixture
def client():
    from src.app import app as kix_app

    kix_app.config["TESTING"] = True
    with kix_app.test_client() as client:
        yield client


def test_runner_state_roundtrip() -> None:
    db_path = Path(__file__).resolve().parent.parent / "data" / "test.sqlite"
    store = RunnerStateStore(str(db_path))
    store.upsert("RLM-GRAPH", "running", 1234, "2026-07-27T22:00:00+00:00", "2026-07-27T22:01:00+00:00")
    record = store.get("RLM-GRAPH")
    assert record is not None
    assert record.status == "running"
    assert record.pid == 1234
    all_records = store.list_all()
    assert "RLM-GRAPH" in all_records


def test_known_repositories_loader() -> None:
    runners = _load_known_repositories()
    assert len(runners) > 0
    names = {r.name for r in runners}
    assert "KIX" in names
    assert "RLM-GRAPH" in names


def test_probe_audit_returns_aggregate(client) -> None:
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {"status": "ok", "service": "rlm-graph", "port": 8786}
    with patch("src.app.requests.get", return_value=fake_response) as mock_get:
        resp = client.get("/probe/audit")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["service"] == "kix"
        assert "results" in data
        assert "healthy" in data
        assert "unhealthy" in data
        assert "phi_cps" in data
        assert 0.0 <= data["phi_cps"] <= 1.0
        assert mock_get.called


def test_action_audit_requires_admin_token(client, tmp_path: Path) -> None:
    from src.auth import create_token
    from src.audit_log import AuditLogStore

    audit_db = str(tmp_path / "audit.db")
    store = AuditLogStore(audit_db)
    store.record("runner_start", "/runners/X/start", "POST", "admin", details="test")
    token = create_token("admin", "admin")
    with patch("src.app.AUDIT_LOG", store):
        resp = client.get("/audit", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["service"] == "kix"
        assert data["count"] == 1
        assert data["audit"][0]["action"] == "runner_start"


def test_alerts_returns_items(client) -> None:
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {"status": "ok", "service": "rlm-graph", "port": 8786}
    with patch("src.app.requests.get", return_value=fake_response):
        resp = client.get("/alerts")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "triggered" in data
        assert "phi_cps" in data
        assert "threshold" in data
        assert "items" in data
        assert data["threshold"] == 0.9


def test_alerts_filters_by_service(client) -> None:
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {"status": "ok", "service": "rlm-graph", "port": 8786}
    with patch("src.app.requests.get", return_value=fake_response):
        resp = client.get("/alerts?service=RLM-GRAPH")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["service"] == "kix"


def test_dashboard_returns_html(client) -> None:
    resp = client.get("/dashboard")
    assert resp.status_code == 200
    assert resp.content_type.startswith("text/html")
    assert b"KIX Dashboard" in resp.data
    assert b"\xcf\x86-CPS History" in resp.data  # UTF-8 for φ-CPS


def test_events_returns_sse(client) -> None:
    resp = client.get("/events")
    assert resp.status_code == 200
    assert resp.content_type.startswith("text/event-stream")


def test_notifications_history_empty(client) -> None:
    resp = client.get("/notifications/history")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["service"] == "kix"
    assert data["count"] == 0
    assert data["notifications"] == []


def test_notifications_history_with_data(client, tmp_path: Path) -> None:
    from src.app import NOTIFICATIONS
    test_db = tmp_path / "notifications.db"
    # Patch NOTIFICATIONS to use temp db
    with patch("src.app.NOTIFICATIONS") as mock_notif:
        from src.notification_store import NotificationStore
        store = NotificationStore(test_db)
        mock_notif.list_recent.return_value = [
            NotificationRecord(
                id=1,
                event="phi_cps_degraded",
                timestamp="2026-07-28T04:00:00+00:00",
                phi_cps=0.7,
                threshold=0.9,
                consecutive_cycles=3,
                service="RLM-GRAPH",
                channel="webhook",
                payload='{"items": []}',
            )
        ]
        resp = client.get("/notifications/history?limit=10")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["count"] == 1
        assert data["notifications"][0]["service"] == "RLM-GRAPH"


def test_notifications_history_filters_by_service(client, tmp_path: Path) -> None:
    from src.app import NOTIFICATIONS
    with patch("src.app.NOTIFICATIONS") as mock_notif:
        from src.notification_store import NotificationStore
        store = NotificationStore(tmp_path / "notifications.db")
        mock_notif.list_recent.return_value = []
        resp = client.get("/notifications/history?service=RLM-GRAPH")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["count"] == 0
        args, kwargs = mock_notif.list_recent.call_args
        assert kwargs.get("service") == "RLM-GRAPH"


def test_metrics_includes_notifications(client, tmp_path: Path) -> None:
    from src.app import METRICS
    with patch("src.app.METRICS") as mock_metrics:
        mock_metrics.list_all.return_value = {
            "webhook": NotificationMetrics(channel="webhook", total_sent=10, total_success=9, total_failed=1, avg_latency_ms=120.5, last_sent_at="2026-07-28T04:00:00+00:00"),
        }
        resp = client.get("/metrics")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "notifications" in data
        assert data["notifications"]["webhook"]["total_sent"] == 10
        assert data["notifications"]["webhook"]["success_rate"] == 0.9


def test_metrics_prometheus_endpoint(client, tmp_path: Path) -> None:
    from src.app import METRICS
    with patch("src.app.METRICS") as mock_metrics:
        mock_metrics.list_all.return_value = {
            "webhook": NotificationMetrics(channel="webhook", total_sent=10, total_success=9, total_failed=1, avg_latency_ms=120.5, last_sent_at="2026-07-28T04:00:00+00:00"),
        }
        resp = client.get("/metrics/prometheus")
        assert resp.status_code == 200
        assert resp.content_type.startswith("text/plain")
        text = resp.get_data(as_text=True)
        assert 'kix_notification_total_total{channel="webhook"} 10' in text
        assert 'kix_notification_success_total{channel="webhook"} 9' in text
        assert 'kix_notification_failed_total{channel="webhook"} 1' in text


def test_dashboard_includes_metrics_section(client, tmp_path: Path) -> None:
    from src.app import METRICS
    with patch("src.app.METRICS") as mock_metrics:
        mock_metrics.list_all.return_value = {
            "webhook": NotificationMetrics(channel="webhook", total_sent=10, total_success=9, total_failed=1, avg_latency_ms=120.5, last_sent_at="2026-07-28T04:00:00+00:00"),
        }
        resp = client.get("/dashboard")
        assert resp.status_code == 200
        assert b"Notification Metrics" in resp.data
        assert b"webhook" in resp.data


def test_remediation_status_empty(client, tmp_path: Path) -> None:
    from src.auth import create_token

    remediation_db = str(tmp_path / "remediation.db")
    token = create_token("admin", "admin")
    with patch.dict(os.environ, {"KIX_REMEDIATION_DB": remediation_db}):
        resp = client.get("/remediation/status", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["service"] == "kix"
        assert data["count"] == 0
        assert data["remediations"] == []


def test_remediation_status_with_data(client, tmp_path: Path) -> None:
    import sqlite3
    from datetime import datetime, timezone
    from src.auto_remediation import RemediationStore
    from src.auth import create_token

    remediation_db = tmp_path / "remediation.db"
    store = RemediationStore(remediation_db)
    store.record(
        RemediationResult(
            policy_id="restart-unreachable-runner",
            service="RLM-GRAPH",
            action_type="restart_runner",
            success=True,
            detail="restart triggered",
            timestamp="2026-07-28T05:00:00+00:00",
        )
    )
    token = create_token("admin", "admin")
    with patch.dict(os.environ, {"KIX_REMEDIATION_DB": str(remediation_db)}):
        resp = client.get("/remediation/status", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["count"] == 1
        assert data["remediations"][0]["policy_id"] == "restart-unreachable-runner"
        assert data["remediations"][0]["service"] == "RLM-GRAPH"

