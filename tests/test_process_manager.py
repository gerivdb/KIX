"""Tests ProcessManager — PID Registry, Singleton Bind, fingerprint."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from src.process_manager import (
    PIDRegistry,
    ProcessManager,
    ProcessEntry,
    SingletonBindManager,
)


@pytest.fixture()
def tmp_state_file():
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    yield Path(path)
    Path(path).unlink(missing_ok=True)


@pytest.fixture()
def registry(tmp_state_file):
    return PIDRegistry(state_file=tmp_state_file)


@pytest.fixture()
def manager(registry):
    return ProcessManager(registry=registry)


# ---------------------------------------------------------------------------
# PIDRegistry
# ---------------------------------------------------------------------------

class TestPIDRegistry:
    def test_register_and_get(self, registry):
        entry = ProcessEntry(
            pid=1234,
            name="test-service",
            repo="TEST",
            role="runner",
            port=8800,
            started_at="2026-09-22T00:00:00+00:00",
            last_seen="2026-09-22T00:00:00+00:00",
            fingerprint="abc123",
        )
        registry.register(entry)
        assert registry.get(1234) is entry

    def test_unregister(self, registry):
        entry = ProcessEntry(
            pid=1234,
            name="test-service",
            repo="TEST",
            role="runner",
            port=8800,
            started_at="2026-09-22T00:00:00+00:00",
            last_seen="2026-09-22T00:00:00+00:00",
            fingerprint="abc123",
        )
        registry.register(entry)
        registry.unregister(1234)
        assert registry.get(1234) is None

    def test_find_by_port(self, registry):
        entry = ProcessEntry(
            pid=1234,
            name="test-service",
            repo="TEST",
            role="runner",
            port=8800,
            started_at="2026-09-22T00:00:00+00:00",
            last_seen="2026-09-22T00:00:00+00:00",
            fingerprint="abc123",
        )
        registry.register(entry)
        assert registry.find_by_port(8800) is entry
        assert registry.find_by_port(9999) is None

    def test_find_by_name(self, registry):
        e1 = ProcessEntry(
            pid=1, name="svc", repo="R", role="r", port=1,
            started_at="2026-09-22T00:00:00+00:00", last_seen="2026-09-22T00:00:00+00:00", fingerprint="f1",
        )
        e2 = ProcessEntry(
            pid=2, name="svc", repo="R", role="r", port=2,
            started_at="2026-09-22T00:00:00+00:00", last_seen="2026-09-22T00:00:00+00:00", fingerprint="f2",
        )
        registry.register(e1)
        registry.register(e2)
        assert len(registry.find_by_name("svc")) == 2

    def test_persistence(self, tmp_state_file):
        reg = PIDRegistry(state_file=tmp_state_file)
        entry = ProcessEntry(
            pid=999,
            name="persist",
            repo="R",
            role="r",
            port=1,
            started_at="2026-09-22T00:00:00+00:00",
            last_seen="2026-09-22T00:00:00+00:00",
            fingerprint="fp",
        )
        reg.register(entry)
        reg2 = PIDRegistry(state_file=tmp_state_file)
        assert reg2.get(999) is not None
        assert reg2.get(999).name == "persist"


# ---------------------------------------------------------------------------
# SingletonBindManager
# ---------------------------------------------------------------------------

class TestSingletonBindManager:
    def test_preflight_port_libre(self, registry):
        mgr = SingletonBindManager(registry)
        result = mgr.preflight(9999, "test-service")
        assert result.ok is True
        assert result.action == "ok"

    def test_preflight_port_occupied_in_registry(self, registry, monkeypatch):
        entry = ProcessEntry(
            pid=1111,
            name="existing",
            repo="R",
            role="r",
            port=49999,
            started_at="2026-09-22T00:00:00+00:00",
            last_seen="2026-09-22T00:00:00+00:00",
            fingerprint="fp",
        )
        registry.register(entry)
        monkeypatch.setattr('src.process_manager._is_process_alive', lambda pid: pid == 1111)
        mgr = SingletonBindManager(registry)
        result = mgr.preflight(49999, "test-service")
        assert result.ok is False
        assert result.action == "bloque"
        assert result.existing_pid == 1111

    def test_fingerprint_mismatch(self, registry, monkeypatch):
        entry = ProcessEntry(
            pid=1111,
            name="existing",
            repo="R",
            role="r",
            port=49998,
            started_at="2026-09-22T00:00:00+00:00",
            last_seen="2026-09-22T00:00:00+00:00",
            fingerprint="old-fp",
        )
        registry.register(entry)
        monkeypatch.setattr('src.process_manager._is_process_alive', lambda pid: pid == 1111)
        mgr = SingletonBindManager(registry)
        result = mgr.preflight(49998, "test-service", expected_fingerprint="new-fp")
        assert result.ok is False
        assert result.action == "warn"


# ---------------------------------------------------------------------------
# ProcessManager (façade)
# ---------------------------------------------------------------------------

class TestProcessManager:
    def test_register_and_list(self, manager):
        entry = manager.register_process(
            pid=5555,
            name="kix",
            repo="KIX",
            role="orchestrator",
            port=8800,
        )
        assert entry.pid == 5555
        processes = manager.list_processes()
        assert len(processes) == 1
        assert processes[0]['name'] == 'kix'

    def test_unregister(self, manager):
        manager.register_process(pid=5555, name="kix", repo="KIX", role="orchestrator", port=8800)
        manager.unregister_process(5555)
        assert manager.get_process(5555) is None

    def test_singleton_check_free(self, manager):
        result = manager.check_singleton(9999, "kix")
        assert result['ok'] is True

    def test_terminate(self, manager, monkeypatch):
        calls = []

        class FakeResult:
            returncode = 0
            stdout = ""
            stderr = ""

        def fake_run(cmd, **kwargs):
            calls.append(cmd)
            return FakeResult()

        monkeypatch.setattr('subprocess.run', fake_run)
        result = manager.terminate(9999)
        assert result['ok'] is True
        assert any('taskkill' in str(c) for c in calls)
