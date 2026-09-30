"""Tests for src/kix/orchestrator/l2_runner_orchestrator.py."""

from __future__ import annotations

import importlib
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.kix.orchestrator.l2_runner_orchestrator import KIXHealthAdapter, KIXProcessManagerAdapter, KIXRegistryAdapter, L2RunnerOrchestrator
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


class TestKIXProcessManagerAdapter:
    def test_register(self):
        process_manager = MagicMock()
        adapter = KIXProcessManagerAdapter(process_manager=process_manager)
        entry = MagicMock(pid=1234, actor_id="trixd", role="runner", started_at=datetime.now(timezone.utc), last_seen=datetime.now(timezone.utc))
        adapter.register(entry)
        process_manager.register_process.assert_called_once()

    def test_unregister(self):
        process_manager = MagicMock()
        adapter = KIXProcessManagerAdapter(process_manager=process_manager)
        adapter.unregister(1234)
        process_manager.unregister_process.assert_called_once_with(1234)

    def test_get(self):
        process_manager = MagicMock()
        process_manager.get_process.return_value = {"pid": 1234, "name": "trixd", "role": "runner", "started_at": "2026-01-01", "last_seen": "2026-01-02"}
        adapter = KIXProcessManagerAdapter(process_manager=process_manager)
        result = adapter.get(1234)
        assert result.pid == 1234

    def test_get_returns_none_when_missing(self):
        process_manager = MagicMock()
        process_manager.get_process.return_value = None
        adapter = KIXProcessManagerAdapter(process_manager=process_manager)
        result = adapter.get(9999)
        assert result is None

    def test_prune_dead(self):
        process_manager = MagicMock()
        process_manager.list_processes.return_value = []
        adapter = KIXProcessManagerAdapter(process_manager=process_manager)
        result = adapter.prune_dead()
        assert result == []


class TestKIXRegistryAdapter:
    def test_load(self):
        registry = {}
        adapter = KIXRegistryAdapter(runner_registry=registry)
        adapter.load()
        assert registry == {}

    def test_get_actor(self):
        spec = RunnerSpec(name="trixd", runner_type="python", port=8742, working_dir=".")
        runner = ConcreteRunner(spec)
        registry = {"trixd": runner}
        adapter = KIXRegistryAdapter(runner_registry=registry)
        actor = adapter.get_actor("trixd")
        assert actor.id == "trixd"

    def test_get_actor_missing(self):
        registry = {}
        adapter = KIXRegistryAdapter(runner_registry=registry)
        assert adapter.get_actor("missing") is None

    def test_list_actors(self):
        spec = RunnerSpec(name="trixd", runner_type="python", port=8742, working_dir=".")
        runner = ConcreteRunner(spec)
        registry = {"trixd": runner}
        adapter = KIXRegistryAdapter(runner_registry=registry)
        assert adapter.list_actors() == ["trixd"]


class TestKIXHealthAdapter:
    def test_check_all_with_check_all(self):
        health_checker = MagicMock()
        health_checker.check_all.return_value = {"status": "ok"}
        adapter = KIXHealthAdapter(health_checker=health_checker)
        result = adapter.check_all()
        assert result["status"] == "ok"

    def test_check_all_without_check_all(self):
        health_checker = MagicMock()
        del health_checker.check_all
        adapter = KIXHealthAdapter(health_checker=health_checker)
        result = adapter.check_all()
        assert result == {}

    def test_check_actor_with_check_runner(self):
        health_checker = MagicMock()
        health_checker.check_runner.return_value = {"status": "ok"}
        adapter = KIXHealthAdapter(health_checker=health_checker)
        result = adapter.check_actor("trixd")
        assert result["status"] == "ok"

    def test_check_actor_without_check_runner(self):
        health_checker = MagicMock()
        del health_checker.check_runner
        adapter = KIXHealthAdapter(health_checker=health_checker)
        result = adapter.check_actor("trixd")
        assert result == {}


class TestL2RunnerOrchestrator:
    def test_create_orchestrator(self):
        registry = {}
        process_manager = MagicMock()
        orchestrator = L2RunnerOrchestrator(runner_registry=registry, process_manager=process_manager)
        assert orchestrator is not None

    def test_import_fallback_branch(self):
        """Lines 25-28: ImportError fallback from process_manager to src.process_manager."""
        with patch.dict("sys.modules", {"process_manager": None}):
            importlib.reload(__import__("src.kix.orchestrator.l2_runner_orchestrator", fromlist=[""]))
