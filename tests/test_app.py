"""Tests for KIX orchestrator."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from flask import Flask
from src.runner_state import RunnerStateStore
from src.app import _load_known_repositories


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


def test_audit_returns_aggregate(client) -> None:
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {"status": "ok", "service": "rlm-graph", "port": 8786}
    with patch("src.app.requests.get", return_value=fake_response) as mock_get:
        resp = client.get("/audit")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["service"] == "kix"
        assert "results" in data
        assert "healthy" in data
        assert "unhealthy" in data
        assert "phi_cps" in data
        assert 0.0 <= data["phi_cps"] <= 1.0
        assert mock_get.called


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


def test_dashboard_returns_html(client) -> None:
    resp = client.get("/dashboard")
    assert resp.status_code == 200
    assert resp.content_type.startswith("text/html")
    assert b"KIX Dashboard" in resp.data


def test_events_returns_sse(client) -> None:
    resp = client.get("/events")
    assert resp.status_code == 200
    assert resp.content_type.startswith("text/event-stream")
