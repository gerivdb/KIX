"""Tests for src/zombie_monitor.py."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.zombie_monitor import (
    _guess_type,
    _is_process_zombie,
    detect_conflicts,
    get_process_zombies,
    get_stash_zombies,
    get_worktree_zombies,
    log_kg_l_edge,
    log_wal,
    purge_zombies,
)


class TestGuessType:
    def test_guess_git(self):
        assert _guess_type("git.exe") == "git"

    def test_guess_node(self):
        assert _guess_type("node.exe") == "node"

    def test_guess_python(self):
        assert _guess_type("python.exe") == "python"

    def test_guess_unknown(self):
        assert _guess_type("unknown.exe") == "unknown"


class TestIsProcessZombie:
    def test_zombie_process(self):
        proc = MagicMock()
        proc.StartTime = __import__("datetime").datetime(2020, 1, 1)
        proc.WorkingSet64 = 5 * 1024 * 1024
        proc.MainWindowTitle = ""
        proc.CPU = 0.1
        now = __import__("datetime").datetime(2026, 1, 1)
        assert _is_process_zombie(proc, now) is True

    def test_not_zombie_has_window(self):
        proc = MagicMock()
        proc.StartTime = __import__("datetime").datetime(2020, 1, 1)
        proc.WorkingSet64 = 5 * 1024 * 1024
        proc.MainWindowTitle = "Some Window"
        proc.CPU = 0.1
        now = __import__("datetime").datetime(2026, 1, 1)
        assert _is_process_zombie(proc, now) is False

    def test_no_start_time(self):
        proc = MagicMock()
        proc.StartTime = None
        assert _is_process_zombie(proc, __import__("datetime").datetime.now()) is False


class TestLogWal:
    def test_log_wal_writes_file(self, tmp_path, monkeypatch):
        wal_dir = tmp_path / ".kilo" / "wal"
        monkeypatch.setattr(
            "src.zombie_monitor.WAL_DIR",
            wal_dir,
        )
        monkeypatch.setattr(
            "src.zombie_monitor.WAL_FILE",
            wal_dir / "zombie-monitor.jsonl",
        )
        log_wal("test_event", {"key": "value"})
        assert (wal_dir / "zombie-monitor.jsonl").exists()

    def test_log_kg_l_edge_writes_file(self, tmp_path, monkeypatch):
        wal_dir = tmp_path / ".kilo" / "wal"
        monkeypatch.setattr(
            "src.zombie_monitor.KG_L_EDGE_FILE",
            wal_dir / "kg-l-edges.jsonl",
        )
        log_kg_l_edge("src", "dst", "prevents", {"key": "value"})
        assert (wal_dir / "kg-l-edges.jsonl").exists()


class TestDetectConflicts:
    def test_detect_conflicts_returns_list(self):
        result = detect_conflicts()
        assert isinstance(result, list)


class TestGetStashZombies:
    def test_get_stash_zombies_success(self):
        output = "stash@{0} 2026-09-20 10:00:00 +0000 temp stash message\n"
        with patch("src.zombie_monitor.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=output, stderr="")
            result = get_stash_zombies()
        assert isinstance(result, list)

    def test_get_stash_zombies_failure(self):
        with patch("src.zombie_monitor.subprocess.run", side_effect=Exception("git failed")):
            result = get_stash_zombies()
        assert result == []


class TestPurgeZombies:
    def test_purge_zombies_dry_run(self, monkeypatch):
        monkeypatch.setattr(
            "src.zombie_monitor.get_process_zombies",
            lambda: [{"type": "git", "pid": 1234, "name": "git.exe"}],
        )
        monkeypatch.setattr(
            "src.zombie_monitor.get_worktree_zombies",
            lambda: [],
        )
        with patch("src.zombie_monitor.log_wal"):
            result = purge_zombies(dry_run=True)
        assert result["status"] == "dry_run"
        assert len(result["purged"]) >= 1

    def test_purge_zombies_no_types(self, monkeypatch):
        monkeypatch.setattr(
            "src.zombie_monitor.get_process_zombies",
            lambda: [],
        )
        monkeypatch.setattr(
            "src.zombie_monitor.get_worktree_zombies",
            lambda: [],
        )
        with patch("src.zombie_monitor.log_wal"):
            result = purge_zombies(dry_run=True)
        assert result["status"] == "dry_run"


class TestGetProcessZombiesBranches:
    def test_known_pids_from_runner_state(self, monkeypatch):
        monkeypatch.setattr("sys.platform", "win32")
        fake_store = MagicMock()
        fake_store.list_all.return_value = {"runner": {"pid": 1111}}
        with patch("src.runner_state.RunnerStateStore", return_value=fake_store):
            fake_psutil = MagicMock()
            fake_proc = MagicMock()
            fake_proc.info = {"pid": 1111, "name": "git.exe", "create_time": 1609459200, "cpu_percent": 0.0, "memory_info": MagicMock(rss=1024 * 1024)}
            fake_psutil.process_iter.return_value = [fake_proc]
            with patch.dict("sys.modules", {"psutil": fake_psutil}):
                with patch("src.zombie_monitor._is_process_zombie", return_value=True):
                    with patch("src.zombie_monitor._guess_type", return_value="git"):
                        result = get_process_zombies()
        assert result == []

    def test_non_win32_returns_empty(self, monkeypatch):
        monkeypatch.setattr("sys.platform", "linux")
        result = get_process_zombies()
        assert result == []

    def test_psutil_loop_exception(self, monkeypatch):
        monkeypatch.setattr("sys.platform", "win32")
        fake_psutil = MagicMock()
        fake_proc = MagicMock()
        fake_proc.info = {"pid": 1111, "name": "git.exe", "create_time": 1609459200, "cpu_percent": 0.0, "memory_info": MagicMock(rss=1024 * 1024)}
        fake_proc.__getitem__ = MagicMock(side_effect=Exception("iteration failed"))
        fake_psutil.process_iter.return_value = [fake_proc]
        monkeypatch.setattr("src.zombie_monitor.psutil", fake_psutil, raising=False)
        result = get_process_zombies()
        assert isinstance(result, list)


class TestGetWorktreeZombiesBranches:
    def test_git_worktree_list_failure(self, monkeypatch):
        with patch("src.zombie_monitor.subprocess.run", side_effect=Exception("git failed")):
            result = get_worktree_zombies()
        assert result == []

    def test_nonzero_returncode(self, monkeypatch):
        with patch("src.zombie_monitor.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
            result = get_worktree_zombies()
        assert result == []


class TestPurgeZombiesBranchesExtended:
    def test_purge_types_filter_excludes(self, monkeypatch):
        monkeypatch.setattr(
            "src.zombie_monitor.get_process_zombies",
            lambda: [{"type": "git", "pid": 1234, "name": "git.exe"}],
        )
        monkeypatch.setattr(
            "src.zombie_monitor.get_worktree_zombies",
            lambda: [],
        )
        with patch("src.zombie_monitor.subprocess.run"):
            with patch("src.zombie_monitor.log_wal"):
                result = purge_zombies(types=["worktree"], dry_run=False)
        assert result["status"] == "purged"
        assert len(result["errors"]) == 0

    def test_purge_worktree_dry_run(self, monkeypatch):
        monkeypatch.setattr(
            "src.zombie_monitor.get_process_zombies",
            lambda: [],
        )
        monkeypatch.setattr(
            "src.zombie_monitor.get_worktree_zombies",
            lambda: [{"path": "/tmp/wt1", "branch": "old-branch", "reason": "branch_deleted"}],
        )
        with patch("src.zombie_monitor.subprocess.run"):
            with patch("src.zombie_monitor.log_wal"):
                result = purge_zombies(dry_run=True)
        assert result["status"] == "dry_run"
        assert result["purged"][0]["action"] == "would_remove"


class TestIsProcessZombieBranches:
    def test_missing_start_time(self):
        import datetime
        proc = MagicMock()
        del proc.StartTime
        assert _is_process_zombie(proc, datetime.datetime.now()) is False

    def test_attribute_error_working_set(self):
        import datetime
        proc = MagicMock()
        proc.StartTime = datetime.datetime.now()
        proc.WorkingSet64 = None
        proc.main_window_title = ""
        proc.cpu = 0.0
        result = _is_process_zombie(proc, datetime.datetime.now())
        assert isinstance(result, bool)


class TestGetWorktreeZombiesBranches:
    def test_worktree_zombies_branch_deleted(self, monkeypatch):
        output = "worktree /tmp/wt1\nHEAD deadbeefdeadbeefdeadbeefdeadbeefdeadbeef\nbranch old-branch\n"
        branch_output = ""
        with patch("src.zombie_monitor.subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout=output, stderr=""),
                MagicMock(returncode=0, stdout=branch_output, stderr=""),
            ]
            result = get_worktree_zombies()
        assert isinstance(result, list)

    def test_worktree_zombies_failure(self, monkeypatch):
        with patch("src.zombie_monitor.subprocess.run", side_effect=Exception("git failed")):
            result = get_worktree_zombies()
        assert result == []

    def test_worktree_zombies_git_failure(self, monkeypatch):
        output = "worktree /tmp/wt1\nHEAD deadbeefdeadbeefdeadbeefdeadbeefdeadbeef\nbranch old-branch\n"
        with patch("src.zombie_monitor.subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout=output, stderr=""),
                MagicMock(returncode=1, stdout="", stderr="error"),
            ]
            result = get_worktree_zombies()
        assert isinstance(result, list)

    def test_worktree_zombies_branch_exists(self, monkeypatch):
        output = "worktree /tmp/wt1\nHEAD deadbeefdeadbeefdeadbeefdeadbeefdeadbeef\nbranch main\n"
        branch_output = "* main\n"
        with patch("src.zombie_monitor.subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout=output, stderr=""),
                MagicMock(returncode=0, stdout=branch_output, stderr=""),
            ]
            result = get_worktree_zombies()
        assert result == []


class TestGetStashZombiesBranches:
    def test_get_stash_zombies_git_failure(self):
        with patch("src.zombie_monitor.subprocess.run", side_effect=Exception("git failed")):
            result = get_stash_zombies()
        assert result == []

    def test_get_stash_zombies_malformed_line(self):
        output = "stash@{0} 2026-09-20\n"
        with patch("src.zombie_monitor.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=output, stderr="")
            result = get_stash_zombies()
        assert result == []

    def test_get_stash_zombies_temp_stash(self):
        output = "stash@{0} 2026-09-20 10:00:00 +0000 temp WIP message\n"
        with patch("src.zombie_monitor.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=output, stderr="")
            with patch("src.zombie_monitor.datetime") as mock_dt:
                now = __import__("datetime").datetime(2026, 9, 27, 10, 0, 0)
                mock_dt.now.return_value = now
                mock_dt.strptime.return_value = now
                result = get_stash_zombies()
        assert len(result) == 1

    def test_get_stash_zombies_non_zero_returncode(self):
        with patch("src.zombie_monitor.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
            result = get_stash_zombies()
        assert result == []


class TestPurgeZombiesBranches:
    def test_purge_processes_win32(self, monkeypatch):
        monkeypatch.setattr("sys.platform", "win32")
        monkeypatch.setattr(
            "src.zombie_monitor.get_process_zombies",
            lambda: [{"type": "git", "pid": 1234, "name": "git.exe"}],
        )
        monkeypatch.setattr(
            "src.zombie_monitor.get_worktree_zombies",
            lambda: [],
        )
        with patch("src.zombie_monitor.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            with patch("src.zombie_monitor.log_wal"):
                result = purge_zombies(dry_run=False)
        assert result["status"] == "purged"
        assert result["wal_logged"] is True

    def test_purge_worktrees(self, monkeypatch):
        monkeypatch.setattr(
            "src.zombie_monitor.get_process_zombies",
            lambda: [],
        )
        monkeypatch.setattr(
            "src.zombie_monitor.get_worktree_zombies",
            lambda: [{"path": "/tmp/wt1", "branch": "old-branch", "reason": "branch_deleted"}],
        )
        with patch("src.zombie_monitor.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            with patch("src.zombie_monitor.log_wal"):
                result = purge_zombies(dry_run=False)
        assert result["status"] == "purged"

    def test_purge_processes_kill_failure(self, monkeypatch):
        monkeypatch.setattr("sys.platform", "win32")
        monkeypatch.setattr(
            "src.zombie_monitor.get_process_zombies",
            lambda: [{"type": "git", "pid": 1234, "name": "git.exe"}],
        )
        monkeypatch.setattr(
            "src.zombie_monitor.get_worktree_zombies",
            lambda: [],
        )
        with patch("src.zombie_monitor.subprocess.run", side_effect=OSError("access denied")):
            with patch("src.zombie_monitor.log_wal"):
                result = purge_zombies(dry_run=False)
        assert result["status"] == "purged"
        assert len(result["errors"]) >= 1


class TestGetProcessZombiesWmi:
    def test_wmi_fallback(self, monkeypatch):
        monkeypatch.setattr("sys.platform", "win32")
        fake_wmi = MagicMock()
        fake_wmi_instance = MagicMock()
        fake_proc = MagicMock()
        fake_proc.Name = "git.exe"
        fake_proc.ProcessId = 1111
        fake_proc.CreationDate = "20260920100000.000000+000"
        fake_proc.MainWindowTitle = ""
        fake_proc.CPU = 0.1
        fake_proc.WorkingSet64 = 5 * 1024 * 1024
        fake_wmi_instance.Win32_Process.return_value = [fake_proc]
        fake_wmi.WMI.return_value = fake_wmi_instance

        import builtins
        import sys
        real_import = builtins.__import__
        psutil_backup = sys.modules.pop("psutil", None)

        def mock_import(*args, **kwargs):
            if args and args[0] == "psutil":
                raise ImportError("No module named 'psutil'")
            return real_import(*args, **kwargs)

        try:
            with patch("builtins.__import__", side_effect=mock_import):
                with patch.dict("sys.modules", {"wmi": fake_wmi}):
                    result = get_process_zombies()
        finally:
            if psutil_backup is not None:
                sys.modules["psutil"] = psutil_backup
        assert len(result) == 1
        assert result[0]["pid"] == 1111
