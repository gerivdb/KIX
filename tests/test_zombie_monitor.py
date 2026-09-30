"""Tests unitaires pour le zombie monitor intelligent."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.zombie_monitor import (
    get_process_zombies,
    get_worktree_zombies,
    purge_zombies,
    _ZOMBIE_PROCESS_NAMES,
)


class TestZombieMonitorPIDRegistry:
    def test_exclude_known_pids(self, tmp_path: Path) -> None:
        """Les PIDs enregistrés dans le PID Registry doivent être exclus."""
        import sqlite3

        db_path = tmp_path / "kix.sqlite"
        conn = sqlite3.connect(db_path)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS runner_state (name TEXT PRIMARY KEY, pid INTEGER, status TEXT)"
        )
        conn.execute("INSERT INTO runner_state VALUES ('kix', 1111, 'running')")
        conn.commit()
        conn.close()

        fake_proc = MagicMock()
        fake_proc.info = {"pid": 1111, "name": "python.exe", "create_time": 0, "cpu_percent": 0, "memory_info": MagicMock(rss=0)}
        with patch("psutil.process_iter", return_value=[fake_proc]):
            zombies = get_process_zombies()
        assert all(z["pid"] != 1111 for z in zombies)

    def test_include_unknown_pids(self, tmp_path: Path) -> None:
        """Les PIDs inconnus restent candidats au filtrage."""
        fake_proc = MagicMock()
        fake_proc.info = {"pid": 9999, "name": "python.exe", "create_time": 0, "cpu_percent": 0, "memory_info": MagicMock(rss=0)}
        with patch("psutil.process_iter", return_value=[fake_proc]), patch("psutil.Process", return_value=MagicMock()):
            with patch("src.zombie_monitor._is_process_zombie", return_value=True):
                zombies = get_process_zombies()
        assert any(z["pid"] == 9999 for z in zombies)

    def test_known_process_names_include_toolchains(self) -> None:
        """La taxonomie inclut les toolchains système."""
        assert "python" in _ZOMBIE_PROCESS_NAMES
        assert "node" in _ZOMBIE_PROCESS_NAMES
        assert "cargo" in _ZOMBIE_PROCESS_NAMES
        assert "git" in _ZOMBIE_PROCESS_NAMES


class TestZombieMonitorWMIFallback:
    def test_wmi_fallback_returns_zombie_when_psutil_missing(self) -> None:
        """Si psutil est absent, le fallback WMI doit renvoyer le processus zombie."""
        import builtins
        import sys
        from unittest.mock import patch

        real_import = builtins.__import__
        psutil_backup = sys.modules.pop("psutil", None)

        def mock_import(*args, **kwargs):
            name = args[0] if args else ""
            if name == "psutil":
                raise ImportError("No module named psutil")
            return real_import(*args, **kwargs)

        fake_wmi_module = MagicMock()
        fake_wmi_instance = MagicMock()
        fake_proc = MagicMock()
        fake_proc.Name = "git.exe"
        fake_proc.ProcessId = 1111
        fake_proc.CreationDate = "20260920100000.000000+000"
        fake_proc.MainWindowTitle = ""
        fake_proc.CPU = 0.1
        fake_proc.WorkingSet64 = 5 * 1024 * 1024
        fake_wmi_instance.Win32_Process.return_value = [fake_proc]
        fake_wmi_module.WMI.return_value = fake_wmi_instance

        try:
            with patch("builtins.__import__", side_effect=mock_import):
                with patch.dict("sys.modules", {"wmi": fake_wmi_module}):
                    zombies = get_process_zombies()
        finally:
            if psutil_backup is not None:
                sys.modules["psutil"] = psutil_backup

        assert len(zombies) == 1
        assert zombies[0]["pid"] == 1111
        assert zombies[0]["name"] == "git.exe"
        assert zombies[0]["note"] == "approximated via WMI"


class TestZombieMonitorWorktreeZombies:
    def test_empty_worktree_list_returns_no_zombies(self) -> None:
        """Si `git worktree list` est vide, aucun worktree zombie n'est retourné."""
        with patch("subprocess.run", return_value=MagicMock(returncode=0, stdout="")):
            zombies = get_worktree_zombies()
        assert zombies == []

    def test_worktree_with_deleted_branch_is_zombie(self) -> None:
        """Un worktree lié à une branche supprimée est détecté comme zombie."""
        porcelain = "worktree D:\\DO\\WEB\\TOOLS\\L4-TOOLS\\CTULU\nbranch feat/test\n"
        branch_list = MagicMock(returncode=0, stdout="")
        with patch("subprocess.run", side_effect=[
            MagicMock(returncode=0, stdout=porcelain),
            branch_list,
        ]):
            zombies = get_worktree_zombies()
        assert len(zombies) == 1
        assert zombies[0]["path"] == "D:\\DO\\WEB\\TOOLS\\L4-TOOLS\\CTULU"
        assert zombies[0]["branch"] == "feat/test"
        assert zombies[0]["reason"] == "branch_deleted"

    def test_worktree_with_existing_branch_is_not_zombie(self) -> None:
        """Un worktree lié à une branche existante n'est pas un zombie."""
        porcelain = "worktree D:\\DO\\WEB\\TOOLS\\L4-TOOLS\\CTULU\nbranch main\n"
        branch_list = MagicMock(returncode=0, stdout="main\n")
        with patch("subprocess.run", side_effect=[
            MagicMock(returncode=0, stdout=porcelain),
            branch_list,
        ]):
            zombies = get_worktree_zombies()
        assert zombies == []

    def test_subprocess_failure_returns_no_zombies(self) -> None:
        """Si `git worktree list` échoue, la fonction retourne une liste vide."""
        with patch("subprocess.run", return_value=MagicMock(returncode=1, stdout="")):
            zombies = get_worktree_zombies()
        assert zombies == []


class TestZombieMonitorPurge:
    def test_dry_run_does_not_kill_process(self) -> None:
        """En dry_run, les processus zombies ne sont pas tués."""
        with patch("src.zombie_monitor.get_process_zombies", return_value=[
            {"pid": 1111, "name": "git.exe", "type": "git", "action": "would_stop"}
        ]), patch("src.zombie_monitor.get_worktree_zombies", return_value=[]), \
             patch("subprocess.run") as mocked_subprocess:
            result = purge_zombies(dry_run=True)

        assert result["status"] == "dry_run"
        assert any(item.get("action") == "would_stop" for item in result["purged"])
        mocked_subprocess.assert_not_called()

    def test_real_purge_kills_process_on_windows(self) -> None:
        """En mode réel sur Windows, taskkill est appelé pour chaque processus zombie."""
        with patch("src.zombie_monitor.get_process_zombies", return_value=[
            {"pid": 2222, "name": "node.exe", "type": "node", "action": "stopped"}
        ]), patch("src.zombie_monitor.get_worktree_zombies", return_value=[]), \
             patch("subprocess.run") as mocked_subprocess, \
             patch("src.zombie_monitor.log_wal") as mocked_log_wal, \
             patch("src.zombie_monitor.log_kg_l_edge") as mocked_log_kg_l:
            result = purge_zombies(dry_run=False)

        assert result["status"] == "purged"
        assert any(item.get("action") == "stopped" for item in result["purged"])
        mocked_subprocess.assert_called_once_with(
            ["taskkill", "/F", "/PID", "2222"],
            capture_output=True,
            timeout=5,
        )
        mocked_log_wal.assert_called_once()
        mocked_log_kg_l.assert_called_once()

    def test_dry_run_marks_worktree_for_removal(self) -> None:
        """En dry_run, les worktrees zombies sont marqués pour suppression."""
        with patch("src.zombie_monitor.get_process_zombies", return_value=[]), \
             patch("src.zombie_monitor.get_worktree_zombies", return_value=[
                 {"path": "D:\\DO\\WEB\\TOOLS\\L4-TOOLS\\CTULU", "branch": "feat/test", "reason": "branch_deleted"}
             ]), \
             patch("subprocess.run") as mocked_subprocess:
            result = purge_zombies(dry_run=True)

        assert any(
            item.get("type") == "worktree" and item.get("action") == "would_remove"
            for item in result["purged"]
        )
        mocked_subprocess.assert_not_called()

    def test_real_purge_removes_worktree(self) -> None:
        """En mode réel, les worktrees zombies sont supprimés via `git worktree remove`."""
        with patch("src.zombie_monitor.get_process_zombies", return_value=[]), \
             patch("src.zombie_monitor.get_worktree_zombies", return_value=[
                 {"path": "D:\\DO\\WEB\\TOOLS\\L4-TOOLS\\CTULU", "branch": "feat/test", "reason": "branch_deleted"}
             ]), \
             patch("subprocess.run") as mocked_subprocess, \
             patch("src.zombie_monitor.log_wal") as mocked_log_wal:
            result = purge_zombies(dry_run=False)

        assert any(
            item.get("type") == "worktree" and item.get("action") == "removed"
            for item in result["purged"]
        )
        mocked_subprocess.assert_called_once_with(
            ["git", "worktree", "remove", "D:\\DO\\WEB\\TOOLS\\L4-TOOLS\\CTULU"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        mocked_log_wal.assert_called_once()

    def test_purge_records_errors_on_failure(self) -> None:
        """Les erreurs de purge sont enregistrées dans le rapport."""
        with patch("src.zombie_monitor.get_process_zombies", return_value=[
            {"pid": 3333, "name": "python.exe", "type": "python", "action": "would_stop"}
        ]), patch("src.zombie_monitor.get_worktree_zombies", return_value=[]), \
             patch("subprocess.run", side_effect=OSError("taskkill failed")), \
             patch("src.zombie_monitor.log_wal"):
            result = purge_zombies(dry_run=False)

        assert len(result["errors"]) == 1
        assert "taskkill failed" in result["errors"][0]
