"""Tests ciblés pour atteindre ≥95% sur src/zombie_monitor.py.

Ces tests couvrent les branches manquantes identifiées par coverage :
- WMI skip/exception branches (lignes 131, 134, 151-154)
- Purge types filter (ligne 310)
- Non-Win32 purge (lignes 323-324)
- Worktree remove failure (lignes 343-344)
- Worktree returncode != 0 (ligne 206)
- psutil loop branches (lignes 168-179)
- Flask routes (lignes 452-469, 475-476)
- list_zombies summary branches (lignes 405-406, 408, 410, 414, 426)
"""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from src.zombie_monitor import (
    detect_conflicts,
    get_process_zombies,
    get_worktree_zombies,
    get_stash_zombies,
    list_zombies,
    purge_zombies,
    zombie_bp,
)


class TestWMIBranches:
    """Couverture des branches WMI dans get_process_zombies."""

    def test_wmi_skip_non_zombie_name(self, monkeypatch):
        """Ligne 131 : skip if name doesn't match zombie patterns."""
        monkeypatch.setattr("sys.platform", "win32")
        fake_wmi = MagicMock()
        fake_proc = MagicMock()
        fake_proc.Name = "not_zombie.exe"
        fake_proc.ProcessId = 1111
        fake_wmi.Win32_Process.return_value = [fake_proc]
        with patch.dict("sys.modules", {"psutil": None, "wmi": fake_wmi}):
            result = get_process_zombies()
        assert result == []

    def test_wmi_skip_known_pid(self, monkeypatch):
        """Ligne 134 : skip if pid in known_pids."""
        monkeypatch.setattr("sys.platform", "win32")
        fake_wmi = MagicMock()
        fake_proc = MagicMock()
        fake_proc.Name = "git.exe"
        fake_proc.ProcessId = 9999
        fake_proc.CreationDate = "20260925120000.000000+000"
        fake_wmi.Win32_Process.return_value = [fake_proc]
        fake_store = MagicMock()
        fake_store.list_all.return_value = {"runner": {"pid": 9999}}
        with patch.dict("sys.modules", {"psutil": None, "wmi": fake_wmi}):
            with patch("src.runner_state.RunnerStateStore", return_value=fake_store):
                result = get_process_zombies()
        assert result == []

    def test_wmi_exception_handling(self, monkeypatch):
        """Lignes 151-154 : exception dans le loop WMI est catchée."""
        monkeypatch.setattr("sys.platform", "win32")
        fake_wmi = MagicMock()
        fake_wmi.Win32_Process.side_effect = RuntimeError("WMI error")
        with patch.dict("sys.modules", {"psutil": None, "wmi": fake_wmi}):
            result = get_process_zombies()
        assert result == []

    def test_wmi_import_error_no_fallback(self, monkeypatch):
        """Ligne 153-154 : ImportError wmi après ImportError psutil."""
        monkeypatch.setattr("sys.platform", "win32")
        with patch.dict("sys.modules", {"psutil": None, "wmi": None}):
            result = get_process_zombies()
        assert result == []


class TestPsutilLoopBranches:
    """Couverture des branches psutil dans get_process_zombies."""

    def test_psutil_loop_with_zombie(self, monkeypatch):
        """Lignes 168-179 : psutil loop avec zombie détecté."""
        monkeypatch.setattr("sys.platform", "win32")
        fake_psutil = MagicMock()
        fake_proc_info = {
            "pid": 1111,
            "name": "git.exe",
            "create_time": 1609459200,
            "cpu_percent": 0.0,
            "memory_info": MagicMock(rss=5 * 1024 * 1024),
        }
        fake_proc = MagicMock()
        fake_proc.info = fake_proc_info
        fake_psutil.process_iter.return_value = [fake_proc]
        fake_psutil_process = MagicMock()
        fake_psutil_process.StartTime = None
        fake_psutil_process.WorkingSet64 = 5 * 1024 * 1024
        fake_psutil_process.MainWindowTitle = ""
        fake_psutil_process.CPU = 0.1
        fake_psutil.Process.return_value = fake_psutil_process
        with patch.dict("sys.modules", {"psutil": fake_psutil}):
            with patch("src.zombie_monitor._is_process_zombie", return_value=True):
                with patch("src.zombie_monitor._guess_type", return_value="git"):
                    result = get_process_zombies()
        assert len(result) == 1
        assert result[0]["pid"] == 1111

    def test_psutil_loop_exception_handling(self, monkeypatch):
        """Lignes 178-179 : exception dans psutil loop est catchée."""
        monkeypatch.setattr("sys.platform", "win32")
        fake_psutil = MagicMock()
        fake_proc = MagicMock()
        fake_proc.info = {
            "pid": 1111,
            "name": "git.exe",
            "create_time": 1609459200,
            "cpu_percent": 0.0,
            "memory_info": MagicMock(rss=1024),
        }
        fake_proc.__getitem__ = MagicMock(side_effect=Exception("iteration failed"))
        fake_psutil.process_iter.return_value = [fake_proc]
        with patch.dict("sys.modules", {"psutil": fake_psutil}):
            result = get_process_zombies()
        assert isinstance(result, list)


class TestPurgeBranches:
    """Couverture des branches de purge_zombies."""

    def test_purge_processes_non_win32(self, monkeypatch):
        """Lignes 323-324 : purge via os.kill sur non-Windows."""
        monkeypatch.setattr("sys.platform", "linux")
        monkeypatch.setattr(
            "src.zombie_monitor.get_process_zombies",
            lambda: [{"type": "git", "pid": 1234, "name": "git"}],
        )
        monkeypatch.setattr("src.zombie_monitor.get_worktree_zombies", lambda: [])
        with patch("src.zombie_monitor.os.kill") as mock_kill:
            with patch("src.zombie_monitor.log_wal"):
                result = purge_zombies(dry_run=False)
        assert result["status"] == "purged"
        mock_kill.assert_called_once_with(1234, 9)

    def test_purge_worktree_remove_failure(self, monkeypatch):
        """Lignes 343-344 : échec git worktree remove."""
        monkeypatch.setattr("sys.platform", "win32")
        monkeypatch.setattr("src.zombie_monitor.get_process_zombies", lambda: [])
        monkeypatch.setattr(
            "src.zombie_monitor.get_worktree_zombies",
            lambda: [{"path": "/tmp/wt1", "branch": "old", "reason": "test"}],
        )
        with patch("src.zombie_monitor.subprocess.run", side_effect=Exception("git failed")):
            with patch("src.zombie_monitor.log_wal"):
                result = purge_zombies(dry_run=False)
        assert result["status"] == "purged"
        assert any("git failed" in e for e in result["errors"])

    def test_purge_types_filter_continue(self, monkeypatch):
        """Ligne 310 : types filter continue sur type non matching."""
        monkeypatch.setattr("sys.platform", "win32")
        monkeypatch.setattr(
            "src.zombie_monitor.get_process_zombies",
            lambda: [{"type": "git", "pid": 1234, "name": "git.exe"}],
        )
        monkeypatch.setattr("src.zombie_monitor.get_worktree_zombies", lambda: [])
        with patch("src.zombie_monitor.log_wal"):
            result = purge_zombies(types=["node"], dry_run=False)
        assert result["purged"] == []
        assert result["status"] == "purged"


class TestWorktreeZombieBranches:
    """Couverture des branches worktree zombies."""

    def test_get_worktree_zombies_git_not_available(self, monkeypatch):
        """Ligne 310 : git non disponible."""
        with patch("src.zombie_monitor.subprocess.run", side_effect=FileNotFoundError):
            result = get_worktree_zombies()
        assert result == []

    def test_get_worktree_zombies_malformed_output(self, monkeypatch):
        """Ligne 323-324 : output mal formé."""
        output = "malformed line without proper format\n"
        with patch("src.zombie_monitor.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=output, stderr="")
            result = get_worktree_zombies()
        assert result == []

    def test_get_worktree_zombies_nonzero_returncode(self, monkeypatch):
        """Ligne 206 : returncode != 0."""
        with patch("src.zombie_monitor.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
            result = get_worktree_zombies()
        assert result == []


class TestStashZombieBranches:
    """Couverture des branches stash zombies."""

    def test_get_stash_zombies_with_valid_entry(self, monkeypatch):
        """Ligne 405-406 : entrée stash valide."""
        output = "stash@{0} 2026-09-20 10:00:00 +0000 feature abc123 WIP message\n"
        with patch("src.zombie_monitor.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=output, stderr="")
            with patch("src.zombie_monitor.datetime") as mock_dt:
                import datetime
                now = datetime.datetime(2026, 9, 27, 10, 0, 0)
                mock_dt.now.return_value = now
                mock_dt.strptime.return_value = now
                result = get_stash_zombies()
        assert len(result) == 1
        assert result[0]["stash_id"] == "stash@{0}"

    def test_get_stash_zombies_recent_entry_not_zombie(self, monkeypatch):
        """Entrée récente non-WIP n'est pas un zombie (skip implicite)."""
        output = "stash@{0} 2026-09-26 10:00:00 +0000 normal stash message\n"
        with patch("src.zombie_monitor.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=output, stderr="")
            with patch("src.zombie_monitor.datetime") as mock_dt:
                import datetime
                now = datetime.datetime(2026, 9, 27, 10, 0, 0)
                recent = datetime.datetime(2026, 9, 26, 10, 0, 0)
                mock_dt.now.return_value = now
                mock_dt.strptime.return_value = recent
                result = get_stash_zombies()
        assert result == []

    def test_get_stash_zombies_wip_message_included(self, monkeypatch):
        """Ligne 410 : message WIP inclus comme temporary."""
        output = "stash@{0} 2026-09-20 10:00:00 +0000 WIP message\n"
        with patch("src.zombie_monitor.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=output, stderr="")
            with patch("src.zombie_monitor.datetime") as mock_dt:
                import datetime
                now = datetime.datetime(2026, 9, 27, 10, 0, 0)
                mock_dt.now.return_value = now
                mock_dt.strptime.return_value = now
                result = get_stash_zombies()
        assert len(result) == 1
        assert result[0]["reason"] == "temporary"

    def test_get_stash_zombies_unknown_format(self, monkeypatch):
        """Ligne 414 : format inconnu."""
        output = "unknown format line\n"
        with patch("src.zombie_monitor.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=output, stderr="")
            result = get_stash_zombies()
        assert result == []


class TestListZombiesRoute:
    """Couverture des branches dans list_zombies."""

    def test_list_zombies_summary_branches(self, monkeypatch):
        """Lignes 405-406, 408, 410 : branches de summary."""
        app = Flask(__name__)
        app.register_blueprint(zombie_bp)
        with app.app_context():
            monkeypatch.setattr(
                "src.zombie_monitor.get_process_zombies",
                lambda: [{"type": "git", "pid": 1, "name": "git"}],
            )
            monkeypatch.setattr(
                "src.zombie_monitor.get_worktree_zombies",
                lambda: [{"path": "/tmp/wt", "branch": "main", "reason": "test"}],
            )
            monkeypatch.setattr(
                "src.zombie_monitor.get_stash_zombies",
                lambda: [{"stash_id": "s1", "message": "msg", "age_days": 1, "reason": "old"}],
            )
            with patch("src.zombie_monitor.log_kg_l_edge"):
                with patch("src.zombie_monitor.log_wal"):
                    result = list_zombies().get_json()
        assert result["summary"]["by_type"]["git"] == 1
        assert result["summary"]["by_type"]["worktree"] == 1
        assert result["summary"]["by_type"]["stash"] == 1
        assert result["summary"]["total"] == 3


class TestFlaskRoutes:
    """Couverture des routes Flask."""

    def test_purge_zombies_endpoint(self, monkeypatch):
        """Lignes 452-469 : purge_zombies_endpoint."""
        app = Flask(__name__)
        app.register_blueprint(zombie_bp)
        with app.app_context():
            monkeypatch.setattr(
                "src.zombie_monitor.get_process_zombies",
                lambda: [{"type": "git", "pid": 1, "name": "git"}],
            )
            monkeypatch.setattr(
                "src.zombie_monitor.get_worktree_zombies",
                lambda: [],
            )
            with patch("src.zombie_monitor.purge_zombies", return_value={"status": "purged"}):
                with app.test_client() as client:
                    resp = client.post(
                        "/health/zombies/purge",
                        json={"types": ["git"], "dry_run": False},
                    )
        assert resp.status_code == 200

    def test_list_conflicts_endpoint(self, monkeypatch):
        """Lignes 475-476 : list_conflicts."""
        app = Flask(__name__)
        app.register_blueprint(zombie_bp)
        with app.app_context():
            with patch("src.zombie_monitor.detect_conflicts", return_value=[]):
                with app.test_client() as client:
                    resp = client.get("/health/conflicts")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] == 0
