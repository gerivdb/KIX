"""Tests unitaires pour GoRunner."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from runners.base import RunnerSpec
from runners.go_runner import GoRunner


@pytest.fixture()
def go_spec(tmp_path: Path) -> RunnerSpec:
    return RunnerSpec(
        name="test-go",
        runner_type="go",
        port=7717,
        working_dir=tmp_path,
        entrypoint="main.go",
        command=["go", "run", "."],
        health_path="/health",
        log_file=tmp_path / "data" / "go.log",
        env={"GOROOT": "C:/DevTools/go"},
    )


class TestGoRunner:
    def test_start_sets_goroot_env(self, go_spec: RunnerSpec) -> None:
        runner = GoRunner(go_spec)
        with patch("subprocess.Popen") as mock_popen, patch.dict(
            os.environ, {"PATH": "C:\\Windows\\system32"}
        ):
            mock_proc = MagicMock()
            mock_proc.pid = 5555
            mock_popen.return_value = mock_proc
            result = runner.start()
        assert result["status"] == "starting"
        assert result["pid"] == 5555
        _, kwargs = mock_popen.call_args
        assert kwargs["env"]["GOROOT"] == "C:/DevTools/go"

    def test_start_writes_log(self, go_spec: RunnerSpec) -> None:
        runner = GoRunner(go_spec)
        with patch("subprocess.Popen") as mock_popen:
            mock_popen.return_value = MagicMock(pid=5555)
            runner.start()
        log_file = go_spec.working_dir / "data" / "go.log"
        assert log_file.exists()
        content = log_file.read_text(encoding="utf-8")
        assert "[KIX] launching" in content

    def test_stop(self, go_spec: RunnerSpec) -> None:
        runner = GoRunner(go_spec)
        with patch("subprocess.run") as mock_run:
            result = runner.stop(1234)
        assert result["status"] == "stopped"
        assert result["pid"] == 1234

    def test_status_alive(self, go_spec: RunnerSpec) -> None:
        runner = GoRunner(go_spec)
        with patch("runners.go_runner._is_process_alive", return_value=True):
            result = runner.status(1234)
        assert result["status"] == "running"

    def test_status_dead(self, go_spec: RunnerSpec) -> None:
        runner = GoRunner(go_spec)
        with patch("runners.go_runner._is_process_alive", return_value=False):
            result = runner.status(1234)
        assert result["status"] == "stopped"

    def test_health_ok(self, go_spec: RunnerSpec) -> None:
        runner = GoRunner(go_spec)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        with patch("requests.get", return_value=mock_resp):
            result = runner.health()
        assert result["status"] == "ok"

    def test_health_unreachable(self, go_spec: RunnerSpec) -> None:
        runner = GoRunner(go_spec)
        with patch("requests.get", side_effect=Exception("conn refused")):
            result = runner.health()
        assert result["status"] == "unreachable"

    def test_logs_empty_when_missing(self, go_spec: RunnerSpec) -> None:
        runner = GoRunner(go_spec)
        assert runner.logs() == ""

    def test_logs_returns_last_lines(self, go_spec: RunnerSpec) -> None:
        log_path = go_spec.working_dir / "data" / "go.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text("line1\nline2\nline3\n", encoding="utf-8")
        runner = GoRunner(go_spec)
        assert runner.logs(lines=2) == "line2\nline3\n"

    def test_restart(self, go_spec: RunnerSpec) -> None:
        runner = GoRunner(go_spec)
        with patch.object(runner, "stop") as mock_stop, patch.object(
            runner, "start"
        ) as mock_start:
            mock_start.return_value = {"status": "starting", "pid": 9999}
            result = runner.restart(1234)
        assert mock_stop.called
        assert mock_start.called
        assert result["status"] == "starting"
