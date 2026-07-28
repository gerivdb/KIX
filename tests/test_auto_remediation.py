"""Tests for auto_remediation."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.auto_remediation import load_policies, evaluate_condition, RemediationStore, RemediationResult


def test_load_policies() -> None:
    policies = load_policies("D:/DO/WEB/TOOLS/L2-PLATFORM/KIX/config/automation.yaml")
    assert len(policies) > 0
    assert any(p["id"] == "restart-unreachable-runner" for p in policies)


def test_load_policies_skips_disabled() -> None:
    policies = load_policies("D:/DO/WEB/TOOLS/L2-PLATFORM/KIX/config/automation.yaml")
    assert all(p.get("enabled", True) for p in policies)


def test_evaluate_condition_equals() -> None:
    assert evaluate_condition({"field": "runner_status", "operator": "==", "value": "unreachable"}, {"runner_status": "unreachable"}) is True
    assert evaluate_condition({"field": "runner_status", "operator": "==", "value": "unreachable"}, {"runner_status": "stopped"}) is False


def test_evaluate_condition_less_than() -> None:
    assert evaluate_condition({"field": "phi_cps", "operator": "<", "value": 0.9}, {"phi_cps": 0.7}) is True
    assert evaluate_condition({"field": "phi_cps", "operator": "<", "value": 0.9}, {"phi_cps": 0.95}) is False


def test_evaluate_condition_greater_equal() -> None:
    assert evaluate_condition({"field": "consecutive_failures", "operator": ">=", "value": 3}, {"consecutive_failures": 3}) is True
    assert evaluate_condition({"field": "consecutive_failures", "operator": ">=", "value": 3}, {"consecutive_failures": 2}) is False


def test_remediation_store_roundtrip(tmp_path: Path) -> None:
    db = tmp_path / "remediation.db"
    store = RemediationStore(db)
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
    items = store.list_recent(limit=10)
    assert len(items) == 1
    assert items[0]["policy_id"] == "restart-unreachable-runner"
    assert items[0]["service"] == "RLM-GRAPH"
    assert items[0]["success"] == 1


def test_remediate_dry_run() -> None:
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {
        "service": "kix",
        "port": 8800,
        "timestamp": 1000000000,
        "triggered": True,
        "phi_cps": 0.7,
        "threshold": 0.9,
        "unhealthy": 1,
        "items": [{"name": "RLM-GRAPH", "status": "unreachable", "port": 8794, "detail": "timeout"}],
    }
    with patch("scripts.auto_remediation.requests.get", return_value=fake_response):
        with patch("scripts.auto_remediation.execute_restart_runner") as mock_restart:
            mock_restart.return_value = (True, "dry-run: would restart RLM-GRAPH")
            with patch("scripts.auto_remediation.execute_send_notification") as mock_notify:
                mock_notify.return_value = (True, "dry-run: notification sent")
                with patch("scripts.auto_remediation.RemediationStore") as mock_store:
                    mock_store.return_value.record.return_value = 1
                    from scripts.auto_remediation import remediate
                    results = remediate("http://localhost:8800", "D:/DO/WEB/TOOLS/L2-PLATFORM/KIX/config/automation.yaml", "mem://", "mem://", True)
                    assert len(results) >= 1
                    assert mock_restart.called or mock_notify.called


def test_remediate_no_items() -> None:
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
    with patch("scripts.auto_remediation.requests.get", return_value=fake_response):
        from scripts.auto_remediation import remediate
        results = remediate("http://localhost:8800", "D:/DO/WEB/TOOLS/L2-PLATFORM/KIX/config/automation.yaml", "mem://", "mem://", True)
        assert len(results) == 0


def test_remediate_filters_by_service() -> None:
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
            {"name": "RLM-GRAPH", "status": "unreachable", "port": 8794, "detail": "timeout"},
            {"name": "RLM-CONFIG", "status": "unreachable", "port": 8793, "detail": "timeout"},
        ],
    }
    with patch("scripts.auto_remediation.requests.get", return_value=fake_response):
        with patch("scripts.auto_remediation.execute_restart_runner") as mock_restart:
            mock_restart.return_value = (True, "dry-run")
            with patch("scripts.auto_remediation.RemediationStore") as mock_store:
                mock_store.return_value.record.return_value = 1
                from scripts.auto_remediation import remediate
                results = remediate("http://localhost:8800", "D:/DO/WEB/TOOLS/L2-PLATFORM/KIX/config/automation.yaml", "mem://", "mem://", True, service_filter="RLM-GRAPH")
                for r in results:
                    assert r.service == "RLM-GRAPH"
