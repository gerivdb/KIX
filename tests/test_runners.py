"""Tests unitaires pour le package runners/ (Phase 1 Foundation)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from runners.base import RunnerSpec, RunnerBase
from runners.registry import RUNNER_CLASSES, get_runner, load_runners_config
from runners.python_runner import PythonRunner
from runners.zig_runner import ZigBinaryRunner
from runners.gateway_runner import GatewayRunner


@pytest.fixture()
def python_spec(tmp_path: Path) -> RunnerSpec:
    return RunnerSpec(
        name="test-python",
        runner_type="python",
        port=9999,
        working_dir=tmp_path,
        entrypoint="main.py",
        health_path="/healthz",
        log_file=tmp_path / "data" / "test.log",
    )


@pytest.fixture()
def zig_spec(tmp_path: Path) -> RunnerSpec:
    return RunnerSpec(
        name="test-trixd",
        runner_type="zig-binary",
        port=7243,
        working_dir=tmp_path,
        binary="zig-out/bin/trixd.exe",
        build={"command": ["zig", "build", "trixd"], "required": True, "pre_start": True},
        health_path="/healthz",
        log_file=tmp_path / "data" / "trixd.log",
    )


@pytest.fixture()
def gateway_spec(tmp_path: Path) -> RunnerSpec:
    return RunnerSpec(
        name="test-gateway",
        runner_type="gateway-exe",
        port=9000,
        working_dir=tmp_path,
        command=["gateway-manager", "start", "--port", "9000"],
        health_path="/health",
        log_file=tmp_path / "data" / "gateway.log",
    )


class TestRunnerSpec:
    def test_defaults(self, tmp_path: Path) -> None:
        spec = RunnerSpec(name="x", runner_type="python", port=1, working_dir=tmp_path)
        assert spec.health_path == "/healthz"
        assert spec.health_timeout == 5.0
        assert spec.bootstrap is False
        assert spec.auto_start is True
        assert spec.restart_policy is None
        assert spec.log_file is None
        assert spec.meta is None


class TestRegistry:
    def test_runner_classes_registered(self) -> None:
        assert "python" in RUNNER_CLASSES
        assert "zig-binary" in RUNNER_CLASSES
        assert "gateway-exe" in RUNNER_CLASSES

    def test_get_runner_unknown_raises(self, tmp_path: Path) -> None:
        spec = RunnerSpec(name="x", runner_type="unknown", port=1, working_dir=tmp_path)
        with pytest.raises(ValueError, match="Unknown runner_type"):
            get_runner(spec)

    def test_get_runner_returns_instance(self, tmp_path: Path) -> None:
        spec = RunnerSpec(name="x", runner_type="python", port=1, working_dir=tmp_path)
        runner = get_runner(spec)
        assert isinstance(runner, PythonRunner)

    def test_load_runners_config_missing(self, tmp_path: Path) -> None:
        result = load_runners_config(tmp_path / "nonexistent.yaml")
        assert result == []

    def test_load_runners_config(self, tmp_path: Path) -> None:
        cfg = tmp_path / "runners.yaml"
        cfg.write_text(
            "runners:\n"
            "  - name: svc\n"
            "    runner_type: python\n"
            "    port: 1234\n"
            "    working_dir: /tmp/svc\n"
            "    entrypoint: app.py\n",
            encoding="utf-8",
        )
        runners = load_runners_config(cfg)
        assert len(runners) == 1
        assert runners[0].name == "svc"
        assert runners[0].port == 1234
        assert runners[0].entrypoint == "app.py"


class TestPythonRunner:
    def test_start_missing_entrypoint(self, python_spec: RunnerSpec) -> None:
        python_spec.entrypoint = None
        runner = PythonRunner(python_spec)
        result = runner.start()
        assert result["status"] == "error"

    def test_start_missing_file(self, python_spec: RunnerSpec) -> None:
        runner = PythonRunner(python_spec)
        result = runner.start()
        assert result["status"] == "error"
        assert "introuvable" in result["detail"]

    def test_start_creates_process(self, python_spec: RunnerSpec) -> None:
        python_spec.entrypoint = "main.py"
        (python_spec.working_dir / "main.py").write_text("print('ok')", encoding="utf-8")
        runner = PythonRunner(python_spec)
        with patch("subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.pid = 4242
            mock_popen.return_value = mock_proc
            result = runner.start()
        assert result["status"] == "starting"
        assert result["pid"] == 4242

    def test_stop(self, python_spec: RunnerSpec) -> None:
        runner = PythonRunner(python_spec)
        with patch("subprocess.run") as mock_run:
            result = runner.stop(1234)
        assert result["status"] == "stopped"
        assert result["pid"] == 1234

    def test_status_alive(self, python_spec: RunnerSpec) -> None:
        runner = PythonRunner(python_spec)
        with patch("runners.python_runner._is_process_alive", return_value=True):
            result = runner.status(1234)
        assert result["status"] == "running"

    def test_status_dead(self, python_spec: RunnerSpec) -> None:
        runner = PythonRunner(python_spec)
        with patch("runners.python_runner._is_process_alive", return_value=False):
            result = runner.status(1234)
        assert result["status"] == "stopped"

    def test_health_ok(self, python_spec: RunnerSpec) -> None:
        runner = PythonRunner(python_spec)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        with patch("requests.get", return_value=mock_resp):
            result = runner.health()
        assert result["status"] == "ok"

    def test_health_unreachable(self, python_spec: RunnerSpec) -> None:
        runner = PythonRunner(python_spec)
        with patch("requests.get", side_effect=Exception("conn refused")):
            result = runner.health()
        assert result["status"] == "unreachable"

    def test_logs_empty_when_missing(self, python_spec: RunnerSpec) -> None:
        runner = PythonRunner(python_spec)
        assert runner.logs() == ""

    def test_logs_returns_last_lines(self, python_spec: RunnerSpec) -> None:
        log_path = python_spec.working_dir / "data" / "test.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text("line1\nline2\nline3\n", encoding="utf-8")
        runner = PythonRunner(python_spec)
        assert runner.logs(lines=2) == "line2\nline3\n"


class TestZigBinaryRunner:
    def test_start_missing_binary(self, zig_spec: RunnerSpec) -> None:
        runner = ZigBinaryRunner(zig_spec)
        result = runner.start()
        assert result["status"] == "error"

    def test_start_build_pre_start_success(self, zig_spec: RunnerSpec) -> None:
        (zig_spec.working_dir / "zig-out" / "bin").mkdir(parents=True)
        (zig_spec.working_dir / "zig-out" / "bin" / "trixd.exe").write_text("", encoding="utf-8")
        runner = ZigBinaryRunner(zig_spec)
        with patch("subprocess.Popen") as mock_popen, patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_proc = MagicMock()
            mock_proc.pid = 5555
            mock_popen.return_value = mock_proc
            result = runner.start()
        assert result["status"] == "starting"
        assert mock_run.called

    def test_start_build_pre_start_failure(self, zig_spec: RunnerSpec) -> None:
        runner = ZigBinaryRunner(zig_spec)
        with patch("subprocess.run", side_effect=Exception("build boom")):
            result = runner.start()
        assert result["status"] == "error"


class TestGatewayRunner:
    def test_start_missing_command(self, gateway_spec: RunnerSpec) -> None:
        gateway_spec.command = None
        runner = GatewayRunner(gateway_spec)
        result = runner.start()
        assert result["status"] == "error"

    def test_start_creates_process(self, gateway_spec: RunnerSpec) -> None:
        runner = GatewayRunner(gateway_spec)
        with patch("subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.pid = 6666
            mock_popen.return_value = mock_proc
            result = runner.start()
        assert result["status"] == "starting"
        assert result["pid"] == 6666
