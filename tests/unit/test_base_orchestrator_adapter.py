"""Tests for KIX base_orchestrator adapter."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add KIX src to path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = REPO_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from base_orchestrator import ActorSpec, ProcessEntry, ProcessManagerInterface, RegistryInterface
from kix.orchestrator.l2_runner_orchestrator import (
    KIXHealthAdapter,
    KIXProcessManagerAdapter,
    KIXRegistryAdapter,
    L2RunnerOrchestrator,
)
from process_manager import ProcessManager
from kix.runner_base import RunnerSpec
from runners.base import RunnerBase


class TestKIXProcessManagerAdapter:
    """Test KIXProcessManagerAdapter implements ProcessManagerInterface."""

    def test_register_and_get(self):
        pm = ProcessManager()
        adapter = KIXProcessManagerAdapter(pm)

        entry = ProcessEntry(
            pid=12345,
            actor_id="test-actor",
            role="actor",
            started_at="2026-09-27T03:00:00",
            last_seen="2026-09-27T03:00:00",
        )
        adapter.register(entry)
        result = adapter.get(12345)
        assert result is not None
        assert result.actor_id == "test-actor"

    def test_unregister(self):
        pm = ProcessManager()
        adapter = KIXProcessManagerAdapter(pm)

        entry = ProcessEntry(
            pid=12346,
            actor_id="test-actor-2",
            role="actor",
            started_at="2026-09-27T03:00:00",
            last_seen="2026-09-27T03:00:00",
        )
        adapter.register(entry)
        adapter.unregister(12346)
        result = adapter.get(12346)
        assert result is None


class TestKIXRegistryAdapter:
    """Test KIXRegistryAdapter implements RegistryInterface."""

    def test_list_actors_empty(self):
        adapter = KIXRegistryAdapter({})
        assert adapter.list_actors() == []

    def test_get_actor_missing(self):
        adapter = KIXRegistryAdapter({})
        assert adapter.get_actor("missing") is None

    def test_get_actor_present(self):
        spec = RunnerSpec(
            name="test-runner",
            runner_type="python",
            port=8080,
            working_dir=Path("/tmp"),
            entrypoint="python main.py",
            auto_start=True,
            meta={"topic": "test"},
        )

        class DummyRunner(RunnerBase):
            def start(self):
                pass
            def stop(self, pid=None):
                pass
            def status(self, pid):
                pass
            def health(self):
                pass
            def logs(self, lines=100):
                pass
            def restart(self):
                pass

        runner = DummyRunner(spec)
        adapter = KIXRegistryAdapter({"test-runner": runner})
        actor = adapter.get_actor("test-runner")
        assert actor is not None
        assert actor.id == "test-runner"
        assert actor.command == "python main.py"
        assert actor.auto_restart is True


class TestKIXHealthAdapter:
    """Test KIXHealthAdapter implements HealthCheckerInterface."""

    def test_check_all_empty(self):
        adapter = KIXHealthAdapter(None)
        result = adapter.check_all()
        assert isinstance(result, dict)

    def test_check_actor_missing(self):
        adapter = KIXHealthAdapter(None)
        result = adapter.check_actor("missing")
        assert isinstance(result, dict)
