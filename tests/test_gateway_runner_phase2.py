"""Tests d'intégration spécifiques GATEWAY-MANAGER (Phase 2).

Valide le wrapper GatewayRunner avec :
- CLI gateway-manager start/stop
- Health-check /health
- Restart policy always
- Logs fichier gateway.log
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from runners.base import RunnerSpec
from runners.gateway_runner import GatewayRunner


@pytest.fixture()
def gm_spec(tmp_path: Path) -> RunnerSpec:
    return RunnerSpec(
        name="gateway-manager",
        runner_type="gateway-exe",
        port=9000,
        working_dir=tmp_path,
        command=["gateway-manager", "start", "--port", "9000"],
        health_path="/health",
        health_timeout=5.0,
        restart_policy="always",
        bootstrap=True,
        log_file=tmp_path / "data" / "gateway.log",
        meta={"repo": "gerivdb/GATEWAY-MANAGER", "role": "BDCP proxy"},
    )


class TestGatewayRunnerPhase2:
    def test_start_launches_cli(self, gm_spec: RunnerSpec) -> None:
        runner = GatewayRunner(gm_spec)
        with patch("subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.pid = 9001
            mock_popen.return_value = mock_proc
            result = runner.start()
        assert result["status"] == "starting"
        assert result["pid"] == 9001
        assert mock_popen.called
        args, kwargs = mock_popen.call_args
        assert args[0] == ["gateway-manager", "start", "--port", "9000"]
        assert kwargs["cwd"] == str(gm_spec.working_dir)

    def test_start_writes_log(self, gm_spec: RunnerSpec) -> None:
        runner = GatewayRunner(gm_spec)
        with patch("subprocess.Popen") as mock_popen:
            mock_popen.return_value = MagicMock(pid=9002)
            runner.start()
        log_path = gm_spec.log_file
        assert log_path.exists()
        content = log_path.read_text(encoding="utf-8")
        assert "gateway-manager start --port 9000" in content

    def test_stop_kills_process(self, gm_spec: RunnerSpec) -> None:
        runner = GatewayRunner(gm_spec)
        with patch("subprocess.run") as mock_run:
            result = runner.stop(9001)
        assert result["status"] == "stopped"
        assert result["pid"] == 9001
        assert mock_run.called

    def test_status_running(self, gm_spec: RunnerSpec) -> None:
        runner = GatewayRunner(gm_spec)
        with patch("runners.gateway_runner._is_process_alive", return_value=True):
            result = runner.status(9001)
        assert result["status"] == "running"

    def test_status_stopped(self, gm_spec: RunnerSpec) -> None:
        runner = GatewayRunner(gm_spec)
        with patch("runners.gateway_runner._is_process_alive", return_value=False):
            result = runner.status(9001)
        assert result["status"] == "stopped"

    def test_health_ok(self, gm_spec: RunnerSpec) -> None:
        runner = GatewayRunner(gm_spec)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        with patch("requests.get", return_value=mock_resp):
            result = runner.health()
        assert result["status"] == "ok"
        assert result["http_status"] == 200

    def test_health_unhealthy(self, gm_spec: RunnerSpec) -> None:
        runner = GatewayRunner(gm_spec)
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        with patch("requests.get", return_value=mock_resp):
            result = runner.health()
        assert result["status"] == "unhealthy"

    def test_health_unreachable(self, gm_spec: RunnerSpec) -> None:
        runner = GatewayRunner(gm_spec)
        with patch("requests.get", side_effect=Exception("conn refused")):
            result = runner.health()
        assert result["status"] == "unreachable"

    def test_logs_empty_when_missing(self, gm_spec: RunnerSpec) -> None:
        runner = GatewayRunner(gm_spec)
        assert runner.logs() == ""

    def test_logs_returns_last_lines(self, gm_spec: RunnerSpec) -> None:
        log_path = gm_spec.working_dir / "data" / "gateway.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text("line1\nline2\nline3\n", encoding="utf-8")
        runner = GatewayRunner(gm_spec)
        assert runner.logs(lines=2) == "line2\nline3\n"

    def test_restart_stops_then_starts(self, gm_spec: RunnerSpec) -> None:
        runner = GatewayRunner(gm_spec)
        with patch("subprocess.run") as mock_run, patch("subprocess.Popen") as mock_popen:
            mock_popen.return_value = MagicMock(pid=9003)
            result = runner.restart(9001)
        assert result["status"] == "starting"
        assert mock_run.called  # stop
        assert mock_popen.called  # start
