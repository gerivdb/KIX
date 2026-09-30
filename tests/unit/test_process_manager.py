"""Tests for src/process_manager.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.process_manager import PIDRegistry, ProcessEntry, ProcessManager, SingletonBindManager, _is_process_alive


class TestProcessEntry:
    def test_to_dict(self):
        entry = ProcessEntry(pid=1234, name="trixd", repo="KIX", role="runner", port=8742, started_at="2026-01-01", last_seen="2026-01-02", fingerprint="abc123")
        data = entry.to_dict()
        assert data["pid"] == 1234
        assert data["name"] == "trixd"
        assert data["fingerprint"] == "abc123"


class TestProcessManager:
    def test_register_and_get_process(self):
        manager = ProcessManager()
        with patch.object(manager._singleton, "probe_fingerprint", return_value=""):
            entry = manager.register_process(pid=1234, name="trixd", repo="KIX", role="runner", port=8742)
        assert entry.pid == 1234
        assert manager.get_process(1234)["name"] == "trixd"

    def test_unregister_process(self):
        manager = ProcessManager()
        with patch.object(manager._singleton, "probe_fingerprint", return_value=""):
            manager.register_process(pid=1234, name="trixd", repo="KIX", role="runner", port=8742)
        manager.unregister_process(1234)
        assert manager.get_process(1234) is None

    def test_list_processes(self):
        manager = ProcessManager()
        with patch.object(manager._singleton, "probe_fingerprint", return_value=""):
            manager.register_process(pid=1234, name="trixd", repo="KIX", role="runner", port=8742)
        processes = manager.list_processes()
        assert len(processes) >= 1

    def test_check_singleton_free(self):
        manager = ProcessManager()
        result = manager.check_singleton(9999, "test-service")
        assert result["ok"] is True

    def test_is_alive(self):
        manager = ProcessManager()
        with patch("src.process_manager._is_process_alive", return_value=True):
            assert manager.is_alive(1234) is True
        with patch("src.process_manager._is_process_alive", return_value=False):
            assert manager.is_alive(1234) is False

    def test_terminate(self):
        manager = ProcessManager()
        with patch("src.process_manager.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            result = manager.terminate(1234)
        assert result["ok"] is True
        assert result["pid"] == 1234


class TestPIDRegistry:
    def test_save_and_load(self, tmp_path):
        from src.process_manager import PIDRegistry, ProcessEntry

        registry = PIDRegistry(state_file=tmp_path / "pid_registry.json")
        entry = ProcessEntry(pid=1234, name="trixd", repo="KIX", role="runner", port=8742, started_at="2026-01-01", last_seen="2026-01-02", fingerprint="abc123")
        registry.register(entry)
        assert registry.get(1234) is not None

        registry2 = PIDRegistry(state_file=tmp_path / "pid_registry.json")
        assert registry2.get(1234).name == "trixd"

    def test_load_missing_file(self, tmp_path):
        from src.process_manager import PIDRegistry

        registry = PIDRegistry(state_file=tmp_path / "missing.json")
        assert registry.list_all() == []

    def test_find_by_port(self):
        manager = ProcessManager()
        with patch.object(manager._singleton, "probe_fingerprint", return_value=""):
            entry = manager.register_process(pid=1234, name="trixd", repo="KIX", role="runner", port=8742)
        found = manager._registry.find_by_port(8742)
        assert found is not None
        assert found.pid == 1234

    def test_find_by_name(self):
        manager = ProcessManager()
        with patch.object(manager._singleton, "probe_fingerprint", return_value=""):
            manager.register_process(pid=1234, name="trixd", repo="KIX", role="runner", port=8742)
        results = manager._registry.find_by_name("trixd")
        assert len(results) >= 1

    def test_prune_dead(self, tmp_path):
        from src.process_manager import PIDRegistry, ProcessEntry

        registry = PIDRegistry(state_file=tmp_path / "pid_registry.json")
        entry = ProcessEntry(pid=1234, name="trixd", repo="KIX", role="runner", port=8742, started_at="2026-01-01", last_seen="2026-01-02", fingerprint="abc123")
        registry.register(entry)
        with patch("src.process_manager._is_process_alive", return_value=False):
            dead = registry.prune_dead()
        assert 1234 in dead


class TestSingletonBindManager:
    def test_preflight_port_in_use(self):
        from src.process_manager import PIDRegistry, SingletonBindManager

        registry = PIDRegistry()
        registry.register(ProcessEntry(pid=1234, name="trixd", repo="KIX", role="runner", port=8742, started_at="2026-01-01", last_seen="2026-01-02", fingerprint="abc123"))
        manager = SingletonBindManager(registry)
        with patch("src.process_manager._is_process_alive", return_value=True):
            result = manager.preflight(8742, "test-service")
        assert result.ok is False
        assert result.action == "bloque"

    def test_preflight_socket_in_use(self):
        from src.process_manager import SingletonBindManager

        manager = SingletonBindManager(PIDRegistry())
        mock_sock = MagicMock()
        with patch("socket.create_connection", return_value=mock_sock):
            result = manager.preflight(8742, "test-service")
        assert result.ok is False
        assert result.action == "bloque"
        assert "déjà utilisé" in result.message

    def test_probe_fingerprint_success(self):
        with patch("src.process_manager.requests.get") as mock_get:
            mock_get.return_value = MagicMock(status_code=200, json=MagicMock(return_value={"build": "abc123"}))
            result = SingletonBindManager.probe_fingerprint(8742)
        assert result == "abc123"

    def test_probe_fingerprint_failure(self):
        with patch("src.process_manager.requests.get", side_effect=Exception("connection failed")):
            result = SingletonBindManager.probe_fingerprint(8742)
        assert result is None


class TestPIDRegistryEdgeCases:
    def test_save_failure(self, tmp_path):
        from src.process_manager import PIDRegistry, ProcessEntry

        registry = PIDRegistry(state_file=tmp_path / "pid_registry.json")
        entry = ProcessEntry(pid=1234, name="trixd", repo="KIX", role="runner", port=8742, started_at="2026-01-01", last_seen="2026-01-02", fingerprint="abc123")
        registry.register(entry)
        with patch("builtins.open", side_effect=OSError("disk full")):
            registry.register(entry)  # second save triggers failure path

    def test_load_failure(self, tmp_path):
        from src.process_manager import PIDRegistry

        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not json", encoding="utf-8")
        registry = PIDRegistry(state_file=bad_file)
        assert registry.list_all() == []


class TestProcessManagerEdgeCases:
    def test_terminate_failure(self, monkeypatch):
        monkeypatch.setattr("sys.platform", "win32")
        manager = ProcessManager()
        with patch("src.process_manager.subprocess.run", side_effect=OSError("access denied")):
            result = manager.terminate(9999)
        assert result["ok"] is False
        assert result["pid"] == 9999

    def test_check_singleton(self, tmp_path):
        from src.process_manager import PIDRegistry, ProcessEntry, ProcessManager

        registry = PIDRegistry(state_file=tmp_path / "pid_registry.json")
        registry.register(ProcessEntry(pid=1234, name="trixd", repo="KIX", role="runner", port=8742, started_at="2026-01-01", last_seen="2026-01-02", fingerprint="abc123"))
        manager = ProcessManager(registry=registry)
        with patch("src.process_manager._is_process_alive", return_value=True):
            result = manager.check_singleton(8742, "test-service")
        assert result["ok"] is False
        assert result["action"] == "bloque"


class TestSingletonBindManagerFingerprintMismatch:
    def test_preflight_fingerprint_mismatch(self):
        from src.process_manager import PIDRegistry, ProcessEntry, SingletonBindManager

        registry = PIDRegistry()
        registry.register(ProcessEntry(pid=1234, name="trixd", repo="KIX", role="runner", port=8742, started_at="2026-01-01", last_seen="2026-01-02", fingerprint="old-fp"))
        manager = SingletonBindManager(registry)
        with patch("src.process_manager._is_process_alive", return_value=True):
            result = manager.preflight(8742, "test-service", expected_fingerprint="new-fp")
        assert result.ok is False
        assert result.action == "warn"
        assert "fingerprint mismatch" in result.message

    def test_preflight_fingerprint_mismatch_after_socket(self):
        from src.process_manager import PIDRegistry, ProcessEntry, SingletonBindManager

        registry = PIDRegistry()
        registry.register(ProcessEntry(pid=1234, name="trixd", repo="KIX", role="runner", port=8742, started_at="2026-01-01", last_seen="2026-01-02", fingerprint="old-fp"))
        manager = SingletonBindManager(registry)
        with patch("src.process_manager._is_process_alive", return_value=False):
            with patch("socket.create_connection", side_effect=OSError("Connection refused")):
                result = manager.preflight(8742, "test-service", expected_fingerprint="new-fp")
        assert result.ok is False
        assert result.action == "warn"


class TestProcessManagerProbeFingerprint:
    def test_probe_fingerprint_via_manager(self):
        manager = ProcessManager()
        with patch("src.process_manager.requests.get") as mock_get:
            mock_get.return_value = MagicMock(status_code=200, json=MagicMock(return_value={"build": "abc123"}))
            result = manager.probe_fingerprint(8742)
        assert result == "abc123"


class TestProcessManagerTerminateNonWindows:
    def test_terminate_non_windows(self, monkeypatch):
        monkeypatch.setattr("sys.platform", "linux")
        manager = ProcessManager()
        with patch("os.kill") as mock_kill:
            result = manager.terminate(1234, force=True)
        assert result["ok"] is True
        assert result["pid"] == 1234
        mock_kill.assert_called_once_with(1234, 9)


class TestIsProcessAliveNonWindows:
    def test_is_alive_linux_true(self, monkeypatch):
        monkeypatch.setattr("sys.platform", "linux")
        with patch("os.kill", side_effect=None):
            assert _is_process_alive(1234) is True

    def test_is_alive_linux_false(self, monkeypatch):
        monkeypatch.setattr("sys.platform", "linux")
        with patch("os.kill", side_effect=ProcessLookupError()):
            assert _is_process_alive(1234) is False
