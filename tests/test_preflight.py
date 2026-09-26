"""Tests preflight KIX — PRD-MOC-KIX-EXE-ORCHESTRATION-2026-09-24."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / 'src'))

from src.app import app
from src.diagnostics import check_toolchains, check_daemon_health, _load_toolchains


class TestToolchainChecks:
    def test_check_toolchains_returns_result(self):
        res = check_toolchains()
        assert res.check == "toolchains"
        assert res.status in {"OK", "WARN", "ERROR"}

    def test_load_toolchains_parses_yaml(self):
        entries = _load_toolchains()
        assert isinstance(entries, list)
        assert any(item.get("name") == "python" for item in entries)


class TestDaemonHealth:
    def test_check_daemon_health_returns_result(self):
        res = check_daemon_health()
        assert res.check == "daemon_health"
        assert res.status in {"OK", "WARN", "ERROR"}


class TestPreflightEndpoints:
    def test_preflight_status(self):
        client = app.test_client()
        resp = client.get("/preflight/status")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "toolchains" in data
        assert "daemons" in data
        assert "status" in data

    def test_preflight_assert_missing(self):
        client = app.test_client()
        resp = client.post("/preflight/assert", json={"require": ["nonexistent-toolchain"]})
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["status"] == "blocked"
        assert "nonexistent-toolchain" in data["missing"]

    def test_preflight_assert_valid(self):
        client = app.test_client()
        resp = client.post("/preflight/assert", json={"require": ["python"]})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] in {"ok", "degraded"}
        assert "nonexistent-toolchain" not in json.dumps(data)

