"""Tests for alert_notifier."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from scripts.alert_notifier import fetch_alerts, send_notification, monitor


def test_fetch_alerts() -> None:
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {
        "service": "kix",
        "port": 8800,
        "timestamp": 1000000000,
        "triggered": True,
        "phi_cps": 0.7,
        "threshold": 0.9,
        "unhealthy": 2,
        "items": [
            {"name": "RLM-GRAPH", "port": 8794, "status": "unreachable", "detail": "timeout"},
        ],
    }
    with patch("scripts.alert_notifier.requests.get", return_value=fake_response) as mock_get:
        data = fetch_alerts("http://localhost:8800", service="RLM-GRAPH")
        assert data["triggered"] is True
        assert data["phi_cps"] == 0.7
        assert mock_get.call_args[1]["params"] == {"service": "RLM-GRAPH"}


def test_fetch_alerts_without_service() -> None:
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {
        "service": "kix",
        "port": 8800,
        "timestamp": 1000000000,
        "triggered": False,
        "phi_cps": 1.0,
        "threshold": 0.9,
        "unhealthy": 0,
        "items": [],
    }
    with patch("scripts.alert_notifier.requests.get", return_value=fake_response) as mock_get:
        data = fetch_alerts("http://localhost:8800")
        assert data["triggered"] is False
        assert mock_get.call_args[1]["params"] == {}


def test_send_notification_with_webhook() -> None:
    with patch("scripts.alert_notifier.requests.post") as mock_post:
        send_notification({"event": "test"}, "http://example.com/webhook")
        assert mock_post.called


def test_send_notification_without_webhook(capsys: pytest.CaptureFixture) -> None:
    send_notification({"event": "test"}, None)
    captured = capsys.readouterr()
    assert "event" in captured.out


def test_monitor_triggers_after_cycles() -> None:
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {
        "service": "kix",
        "port": 8800,
        "timestamp": 1000000000,
        "triggered": True,
        "phi_cps": 0.5,
        "threshold": 0.9,
        "unhealthy": 1,
        "items": [{"name": "RLM-GRAPH", "status": "unreachable"}],
    }
    sleep_calls = 0

    def fake_sleep(seconds: int) -> None:
        nonlocal sleep_calls
        sleep_calls += 1
        if sleep_calls >= 5:
            raise KeyboardInterrupt

    with patch("scripts.alert_notifier.requests.get", return_value=fake_response):
        with patch("scripts.alert_notifier.send_notification") as mock_notify:
            with patch("scripts.alert_notifier.time.sleep", side_effect=fake_sleep):
                rc = monitor("http://localhost:8800", "mem://", 1, 0.9, 3, False, None)
                assert rc == 0
                assert mock_notify.call_count == 1
                payload = mock_notify.call_args[0][0]
                assert payload["event"] == "phi_cps_degraded"
                assert payload["consecutive_cycles"] == 3


def test_monitor_resets_when_not_triggered() -> None:
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {
        "service": "kix",
        "port": 8800,
        "timestamp": 1000000000,
        "triggered": False,
        "phi_cps": 1.0,
        "threshold": 0.9,
        "unhealthy": 0,
        "items": [],
    }
    sleep_calls = 0

    def fake_sleep(seconds: int) -> None:
        nonlocal sleep_calls
        sleep_calls += 1
        if sleep_calls >= 5:
            raise KeyboardInterrupt

    with patch("scripts.alert_notifier.requests.get", return_value=fake_response):
        with patch("scripts.alert_notifier.send_notification") as mock_notify:
            with patch("scripts.alert_notifier.time.sleep", side_effect=fake_sleep):
                monitor("http://localhost:8800", "mem://", 1, 0.9, 3, False, None)
                assert mock_notify.call_count == 0
