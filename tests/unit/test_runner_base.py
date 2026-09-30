"""Tests for src/kix/runner_base.py."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.kix.runner_base import BaseRunner, RunnerSpec


class ConcreteRunner(BaseRunner):
    def start(self) -> dict:
        return {"status": "started"}

    def stop(self, pid=None) -> dict:
        return {"status": "stopped"}

    def status(self, pid: int) -> dict:
        return {"status": "running", "pid": pid}

    def health(self) -> dict:
        return {"status": "ok"}

    def logs(self, lines: int = 100) -> str:
        return "log line 1\nlog line 2"


class TestRunnerSpec:
    def test_create_spec(self):
        spec = RunnerSpec(name="trixd", runner_type="python", port=8742, working_dir=Path("."))
        assert spec.name == "trixd"
        assert spec.port == 8742
        assert spec.runner_type == "python"


class TestBaseRunner:
    def test_create_runner(self):
        spec = RunnerSpec(name="trixd", runner_type="python", port=8742, working_dir=Path("."))
        runner = ConcreteRunner(spec)
        assert runner.spec.name == "trixd"

    def test_start(self):
        spec = RunnerSpec(name="trixd", runner_type="python", port=8742, working_dir=Path("."))
        runner = ConcreteRunner(spec)
        assert runner.start() == {"status": "started"}

    def test_stop(self):
        spec = RunnerSpec(name="trixd", runner_type="python", port=8742, working_dir=Path("."))
        runner = ConcreteRunner(spec)
        assert runner.stop() == {"status": "stopped"}

    def test_status(self):
        spec = RunnerSpec(name="trixd", runner_type="python", port=8742, working_dir=Path("."))
        runner = ConcreteRunner(spec)
        assert runner.status(1234) == {"status": "running", "pid": 1234}

    def test_health(self):
        spec = RunnerSpec(name="trixd", runner_type="python", port=8742, working_dir=Path("."))
        runner = ConcreteRunner(spec)
        assert runner.health() == {"status": "ok"}

    def test_logs(self):
        spec = RunnerSpec(name="trixd", runner_type="python", port=8742, working_dir=Path("."))
        runner = ConcreteRunner(spec)
        assert "log line 1" in runner.logs()

    def test_restart(self):
        spec = RunnerSpec(name="trixd", runner_type="python", port=8742, working_dir=Path("."))
        runner = ConcreteRunner(spec)
        with patch.object(runner, "stop", return_value={"status": "stopped"}):
            with patch.object(runner, "start", return_value={"status": "started"}):
                result = runner.restart(1234)
        assert result["status"] == "started"

    def test_metrics(self):
        spec = RunnerSpec(name="trixd", runner_type="python", port=8742, working_dir=Path("."))
        runner = ConcreteRunner(spec)
        metrics = runner.metrics()
        assert metrics["runner"] == "trixd"
        assert metrics["port"] == 8742

    def test_wazaa_publish(self):
        spec = RunnerSpec(name="trixd", runner_type="python", port=8742, working_dir=Path("."))
        runner = ConcreteRunner(spec)
        runner.wazaa_publish("test-topic", {"key": "value"})


class TestBaseRunnerAbstractBranches:
    def test_abstract_methods_raise_not_implemented(self):
        spec = RunnerSpec(name="trixd", runner_type="python", port=8742, working_dir=Path("."))
        # Create a minimal subclass that does NOT implement abstract methods,
        # then force-instance it to exercise the base raise NotImplementedError.
        class MinimalRunner(BaseRunner):
            pass

        MinimalRunner.__abstractmethods__ = frozenset()
        runner = MinimalRunner(spec)
        for method_name, args in [
            ("start", ()),
            ("stop", (1234,)),
            ("status", (1234,)),
            ("health", ()),
            ("logs", ()),
        ]:
            with pytest.raises(NotImplementedError):
                getattr(runner, method_name)(*args)

    def test_restart_stop_failure(self):
        spec = RunnerSpec(name="trixd", runner_type="python", port=8742, working_dir=Path("."))
        runner = ConcreteRunner(spec)
        with patch.object(runner, "stop", return_value={"status": "failed"}):
            result = runner.restart(1234)
        assert result["status"] == "failed"

    def test_handle_sigterm_calls_stop(self):
        spec = RunnerSpec(name="trixd", runner_type="python", port=8742, working_dir=Path("."))
        runner = ConcreteRunner(spec)
        with patch.object(runner, "stop", return_value={"status": "stopped"}) as mock_stop:
            runner._handle_sigterm(15, None)
        mock_stop.assert_called_once()

    def test_handle_sigint_calls_stop(self):
        spec = RunnerSpec(name="trixd", runner_type="python", port=8742, working_dir=Path("."))
        runner = ConcreteRunner(spec)
        with patch.object(runner, "stop", return_value={"status": "stopped"}) as mock_stop:
            runner._handle_sigint(2, None)
        mock_stop.assert_called_once()
