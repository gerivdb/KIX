"""Tests for src/runner_state.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.runner_state import RunnerRecord, RunnerStateStore


class TestRunnerRecord:
    def test_create_record(self):
        record = RunnerRecord(name="trixd", status="running", pid=1234, started_at="2026-01-01", updated_at="2026-01-02")
        assert record.name == "trixd"
        assert record.status == "running"
        assert record.pid == 1234
        assert record.started_at == "2026-01-01"
        assert record.updated_at == "2026-01-02"


class TestRunnerStateStore:
    def test_upsert_and_get(self, tmp_path):
        db = tmp_path / "runners.db"
        store = RunnerStateStore(db)
        store.upsert("trixd", "running", 1234, "2026-01-01", "2026-01-02")
        record = store.get("trixd")
        assert record.name == "trixd"
        assert record.status == "running"
        assert record.pid == 1234
        assert record.started_at == "2026-01-01"
        assert record.updated_at == "2026-01-02"

    def test_get_missing_returns_none(self, tmp_path):
        db = tmp_path / "runners.db"
        store = RunnerStateStore(db)
        assert store.get("missing") is None

    def test_list_all(self, tmp_path):
        db = tmp_path / "runners.db"
        store = RunnerStateStore(db)
        store.upsert("trixd", "running", 1234, "2026-01-01", "2026-01-02")
        store.upsert("ctulu", "running", 5678, "2026-01-01", "2026-01-02")
        all_runners = store.list_all()
        assert len(all_runners) == 2
        assert all_runners["trixd"].status == "running"
        assert all_runners["ctulu"].status == "running"

    def test_register_git_process_korx_none(self, tmp_path):
        db = tmp_path / "runners.db"
        store = RunnerStateStore(db)
        with patch.object(store, "_get_korx", return_value=None):
            assert store.register_git_process(1234) is False

    def test_unregister_git_process_korx_none(self, tmp_path):
        db = tmp_path / "runners.db"
        store = RunnerStateStore(db)
        with patch.object(store, "_get_korx", return_value=None):
            store.unregister_git_process(1234)

    def test_get_git_semaphore_state_korx_none(self, tmp_path):
        db = tmp_path / "runners.db"
        store = RunnerStateStore(db)
        with patch.object(store, "_get_korx", return_value=None):
            state = store.get_git_semaphore_state()
        assert state["available"] is True
        assert state["git_count"] == 0

    def test_get_phi_cps_korx_none(self, tmp_path):
        db = tmp_path / "runners.db"
        store = RunnerStateStore(db)
        with patch.object(store, "_get_korx", return_value=None):
            phi = store.get_phi_cps()
        assert phi == 4.559


class TestRunnerStateStoreWithKorx:
    def test_get_korx_creates_instance(self, tmp_path):
        db = tmp_path / "runners.db"
        store = RunnerStateStore(db)
        mock_korx = MagicMock()
        with patch.dict("sys.modules", {"kix.immune": MagicMock()}):
            with patch.object(store, "_get_korx", return_value=mock_korx):
                pass

    def test_register_git_process_with_korx(self, tmp_path):
        db = tmp_path / "runners.db"
        store = RunnerStateStore(db)
        mock_korx = MagicMock()
        mock_korx.register_git_process.return_value = True
        with patch.object(store, "_get_korx", return_value=mock_korx):
            assert store.register_git_process(1234) is True

    def test_unregister_git_process_with_korx(self, tmp_path):
        db = tmp_path / "runners.db"
        store = RunnerStateStore(db)
        mock_korx = MagicMock()
        with patch.object(store, "_get_korx", return_value=mock_korx):
            store.unregister_git_process(1234)
        mock_korx.unregister_git_process.assert_called_once_with(1234)

    def test_get_git_semaphore_state_with_korx(self, tmp_path):
        db = tmp_path / "runners.db"
        store = RunnerStateStore(db)
        mock_korx = MagicMock()
        mock_korx.can_spawn_git.return_value = True
        mock_korx.read_git_count.return_value = 2
        mock_korx.read_git_pids.return_value = [1234, 5678]
        with patch.object(store, "_get_korx", return_value=mock_korx):
            state = store.get_git_semaphore_state()
        assert state["available"] is True
        assert state["git_count"] == 2

    def test_get_phi_cps_with_korx(self, tmp_path):
        db = tmp_path / "runners.db"
        store = RunnerStateStore(db)
        mock_korx = MagicMock()
        mock_korx.read_phi_cps.return_value = 3.14
        with patch.object(store, "_get_korx", return_value=mock_korx):
            phi = store.get_phi_cps()
        assert phi == 3.14

    def test_transaction_rollback(self, tmp_path):
        db = tmp_path / "runners.db"
        store = RunnerStateStore(db)
        store.upsert("trixd", "running", 1234, "2026-01-01", "2026-01-02")
        try:
            with store.transaction() as conn:
                conn.execute("INSERT INTO runners (name, status, pid, started_at, updated_at) VALUES (?, ?, ?, ?, ?)", ("bad", "bad", 0, "2026-01-01", "2026-01-02"))
                raise ValueError("force rollback")
        except ValueError:
            pass
        assert store.get("bad") is None


class TestRunnerStateStoreKorxBranches:
    def test_get_korx_import_failure(self, tmp_path):
        db = tmp_path / "runners.db"
        store = RunnerStateStore(db)
        with patch.dict("sys.modules", {"kix.immune": None}):
            korx = store._get_korx()
        assert korx is None

    def test_get_korx_import_success(self, tmp_path):
        db = tmp_path / "runners.db"
        store = RunnerStateStore(db)
        mock_korx = MagicMock()
        with patch.dict("sys.modules", {"kix.immune": MagicMock(KORXStateKernel=MagicMock(return_value=mock_korx))}):
            korx = store._get_korx()
        assert korx is mock_korx

    def test_upsert_kg_l_bridge_failure(self, tmp_path):
        db = tmp_path / "runners.db"
        store = RunnerStateStore(db)
        with patch.dict("sys.modules", {"kix_bridge_wazaa": None}):
            store.upsert("trixd", "running", 1234, "2026-01-01", "2026-01-02")
        assert store.get("trixd").name == "trixd"
