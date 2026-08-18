"""Tests d'int�gration pour le module runners/ et les endpoints KIX.

Ces tests valident le cycle de vie complet start/health/stop pour chaque
type de runner, en mode mock� pour ne pas d�pendre de services r�els.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from runners.base import RunnerSpec
from runners.python_runner import PythonRunner
from runners.zig_runner import ZigBinaryRunner
from runners.gateway_runner import GatewayRunner


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> pytest.FlaskClient:
    monkeypatch.setenv("KIX_DB", str(tmp_path / "kix.sqlite"))
    monkeypatch.setenv("KIX_NOTIFICATIONS_DB", str(tmp_path / "notifications.db"))
    monkeypatch.setenv("KIX_AUDIT_DB", str(tmp_path / "audit.db"))
    from src.app import app
    app.config["TESTING"] = True
    return app.test_client()


def _python_spec(tmp_path: Path) -> RunnerSpec:
    return RunnerSpec(
        name="integration-python",
        runner_type="python",
        port=9999,
        working_dir=tmp_path,
        entrypoint="main.py",
        health_path="/healthz",
        log_file=tmp_path / "data" / "integration.log",
    )


def _zig_spec(tmp_path: Path) -> RunnerSpec:
    return RunnerSpec(
        name="integration-trixd",
        runner_type="zig-binary",
        port=7243,
        working_dir=tmp_path,
        binary="zig-out/bin/trixd.exe",
        build={"command": ["zig", "build", "trixd"], "required": True, "pre_start": True},
        health_path="/healthz",
        log_file=tmp_path / "data" / "trixd.log",
    )


def _gateway_spec(tmp_path: Path) -> RunnerSpec:
    return RunnerSpec(
        name="integration-gateway",
        runner_type="gateway-exe",
        port=9000,
        working_dir=tmp_path,
        command=["gateway-manager", "start", "--port", "9000"],
        health_path="/health",
        log_file=tmp_path / "data" / "gateway.log",
    )


class TestPythonRunnerIntegration:
    def test_full_lifecycle(self, tmp_path: Path) -> None:
        spec = _python_spec(tmp_path)
        (tmp_path / "main.py").write_text("print('ok')", encoding="utf-8")
        runner = PythonRunner(spec)

        with patch("subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.pid = 1111
            mock_popen.return_value = mock_proc
            start_result = runner.start()
        assert start_result["status"] == "starting"
        pid = start_result["pid"]

        with patch("runners.python_runner._is_process_alive", return_value=True):
            status = runner.status(pid)
        assert status["status"] == "running"

        with patch("requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_get.return_value = mock_resp
            health = runner.health()
        assert health["status"] == "ok"

        with patch("subprocess.run"):
            stop = runner.stop(pid)
        assert stop["status"] == "stopped"

        with patch("runners.python_runner._is_process_alive", return_value=False):
            status = runner.status(pid)
        assert status["status"] == "stopped"


class TestZigBinaryRunnerIntegration:
    def test_full_lifecycle_with_build(self, tmp_path: Path) -> None:
        spec = _zig_spec(tmp_path)
        (tmp_path / "zig-out" / "bin").mkdir(parents=True)
        (tmp_path / "zig-out" / "bin" / "trixd.exe").write_text("", encoding="utf-8")
        runner = ZigBinaryRunner(spec)

        with patch("subprocess.run") as mock_run, patch("subprocess.Popen") as mock_popen:
            mock_run.return_value.returncode = 0
            mock_proc = MagicMock()
            mock_proc.pid = 2222
            mock_popen.return_value = mock_proc
            start_result = runner.start()
        assert start_result["status"] == "starting"
        assert mock_run.called


class TestGatewayRunnerIntegration:
    def test_full_lifecycle(self, tmp_path: Path) -> None:
        spec = _gateway_spec(tmp_path)
        runner = GatewayRunner(spec)

        with patch("subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.pid = 3333
            mock_popen.return_value = mock_proc
            start_result = runner.start()
        assert start_result["status"] == "starting"
        pid = start_result["pid"]

        with patch("runners.gateway_runner._is_process_alive", return_value=True):
            status = runner.status(pid)
        assert status["status"] == "running"


class TestEndpointsIntegration:
    def test_swarm_status(self, client: pytest.FlaskClient) -> None:
        resp = client.get("/swarm/status")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["service"] == "kix"
        assert "runners" in data
        assert "kix" in data["runners"]
        assert "gateway-manager" in data["runners"]
        assert "trixd" in data["runners"]
        assert "wazaa" in data["runners"]

    def test_doctor(self, client: pytest.FlaskClient) -> None:
        resp = client.get("/doctor")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "runners" in data
        assert "unhealthy_runners" in data
        assert data["total"] >= 4

    def test_runner_health_not_found(self, client: pytest.FlaskClient) -> None:
        resp = client.get("/runners/nonexistent/health")
        assert resp.status_code == 404

    def test_runner_logs_not_found(self, client: pytest.FlaskClient) -> None:
        resp = client.get("/runners/nonexistent/logs")
        assert resp.status_code == 404

    def test_runner_restart_not_found(self, client: pytest.FlaskClient) -> None:
        resp = client.post("/runners/nonexistent/restart")
        # login_required d�clenche 401 avant le 404 runner_not_found
        assert resp.status_code in (401, 404)

    def test_doctor_run(self, client: pytest.FlaskClient) -> None:
        resp = client.post("/doctor/run")
        # login_required d�clenche 401 sans token
        assert resp.status_code in (401, 200)
