"""Tests unitaires pour NodeRunner."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from runners.base import RunnerSpec
from runners.node_runner import NodeRunner


@pytest.fixture()
def node_spec(tmp_path: Path) -> RunnerSpec:
    return RunnerSpec(
        name="test-node",
        runner_type="node",
        port=7716,
        working_dir=tmp_path,
        entrypoint="server.js",
        command=["node", "server.js"],
        health_path="/health",
        log_file=tmp_path / "data" / "node.log",
    )


class TestNodeRunner:
    def test_start_launches_node(self, node_spec: RunnerSpec) -> None:
        runner = NodeRunner(node_spec)
        with patch("subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.pid = 6666
            mock_popen.return_value = mock_proc
            result = runner.start()
        assert result["status"] == "starting"
        assert result["pid"] == 6666
        assert mock_popen.called

    def test_start_writes_log(self, node_spec: RunnerSpec) -> None:
        runner = NodeRunner(node_spec)
        with patch("subprocess.Popen") as mock_popen:
            mock_popen.return_value = MagicMock(pid=6666)
            runner.start()
        log_file = node_spec.working_dir / "data" / "node.log"
        assert log_file.exists()
        content = log_file.read_text(encoding="utf-8")
        assert "[KIX] launching" in content

    def test_stop(self, node_spec: RunnerSpec) -> None:
        runner = NodeRunner(node_spec)
        with patch("subprocess.run") as mock_run:
            result = runner.stop(1234)
        assert result["status"] == "stopped"
        assert result["pid"] == 1234

    def test_status_alive(self, node_spec: RunnerSpec) -> None:
        runner = NodeRunner(node_spec)
        with patch("runners.node_runner._is_process_alive", return_value=True):
            result = runner.status(1234)
        assert result["status"] == "running"

    def test_status_dead(self, node_spec: RunnerSpec) -> None:
        runner = NodeRunner(node_spec)
        with patch("runners.node_runner._is_process_alive", return_value=False):
            result = runner.status(1234)
        assert result["status"] == "stopped"

    def test_health_ok(self, node_spec: RunnerSpec) -> None:
        runner = NodeRunner(node_spec)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        with patch("requests.get", return_value=mock_resp):
            result = runner.health()
        assert result["status"] == "ok"

    def test_health_unreachable(self, node_spec: RunnerSpec) -> None:
        runner = NodeRunner(node_spec)
        with patch("requests.get", side_effect=Exception("conn refused")):
            result = runner.health()
        assert result["status"] == "unreachable"

    def test_logs_empty_when_missing(self, node_spec: RunnerSpec) -> None:
        runner = NodeRunner(node_spec)
        assert runner.logs() == ""

    def test_logs_returns_last_lines(self, node_spec: RunnerSpec) -> None:
        log_path = node_spec.working_dir / "data" / "node.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text("line1\nline2\nline3\n", encoding="utf-8")
        runner = NodeRunner(node_spec)
        assert runner.logs(lines=2) == "line2\nline3\n"

    def test_restart(self, node_spec: RunnerSpec) -> None:
        runner = NodeRunner(node_spec)
        with patch.object(runner, "stop") as mock_stop, patch.object(
            runner, "start"
        ) as mock_start:
            mock_start.return_value = {"status": "starting", "pid": 9999}
            result = runner.restart(1234)
        assert mock_stop.called
        assert mock_start.called
        assert result["status"] == "starting"
