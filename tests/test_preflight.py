"""Tests unitaires pour les endpoints preflight KIX."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from src.app import app


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> pytest.FlaskClient:
    monkeypatch.setenv("KIX_DB", str(tmp_path / "kix.sqlite"))
    monkeypatch.setenv("KIX_NOTIFICATIONS_DB", str(tmp_path / "notifications.db"))
    monkeypatch.setenv("KIX_AUDIT_DB", str(tmp_path / "audit.db"))
    app.config["TESTING"] = True
    return app.test_client()


class TestPreflightStatus:
    def test_returns_status(self, client: pytest.FlaskClient) -> None:
        with patch("src.diagnostics.run_all_checks") as mock_checks:
            mock_checks.return_value = {
                "checks": [
                    {"check": "toolchains", "status": "OK", "detail": ""},
                    {"check": "daemon_health", "status": "OK", "detail": ""},
                ],
                "error": 0,
                "warn": 0,
                "ok": 2,
            }
            resp = client.get("/preflight/status")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"
        assert "preflight" in data


class TestPreflightAssert:
    def test_assert_pass(self, client: pytest.FlaskClient) -> None:
        with patch("src.diagnostics.run_all_checks") as mock_checks:
            mock_checks.return_value = {
                "checks": [
                    {"check": "toolchains", "status": "OK"},
                    {"check": "daemon_health", "status": "OK"},
                ],
                "error": 0,
            }
            resp = client.post("/preflight/assert", json={"require": ["toolchains", "daemon_health"]})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["ok"] is True

    def test_assert_missing(self, client: pytest.FlaskClient) -> None:
        with patch("src.diagnostics.run_all_checks") as mock_checks:
            mock_checks.return_value = {
                "checks": [
                    {"check": "toolchains", "status": "ERROR"},
                    {"check": "daemon_health", "status": "OK"},
                ],
                "error": 1,
            }
            resp = client.post("/preflight/assert", json={"require": ["toolchains", "daemon_health"]})
        assert resp.status_code == 409
        data = resp.get_json()
        assert data["ok"] is False
        assert "toolchains" in data["missing"]

    def test_assert_empty_require(self, client: pytest.FlaskClient) -> None:
        resp = client.post("/preflight/assert", json={"require": []})
        assert resp.status_code == 400
