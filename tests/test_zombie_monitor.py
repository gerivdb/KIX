"""Tests for KIX zombie monitor."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.app import app as kix_app
from src.zombie_monitor import (
    _guess_type,
    detect_conflicts,
    get_process_zombies,
    get_stash_zombies,
    get_worktree_zombies,
    purge_zombies,
)


@pytest.fixture
def client():
    kix_app.config["TESTING"] = True
    with kix_app.test_client() as client:
        yield client


# ═══════════════════════════════════════════════════════════════════════
# Unit tests — pure functions
# ═══════════════════════════════════════════════════════════════════════

class TestGuessType:
    def test_git(self):
        assert _guess_type("git.exe") == "git"

    def test_node(self):
        assert _guess_type("node.exe") == "node"

    def test_python(self):
        assert _guess_type("python.exe") == "python"

    def test_unknown(self):
        assert _guess_type("unknown.exe") == "unknown"


class TestGetProcessZombies:
    @patch("src.zombie_monitor.psutil", create=True)
    def test_empty(self, mock_psutil: MagicMock) -> None:
        mock_psutil.process_iter.return_value = []
        result = get_process_zombies()
        assert result == []

    @patch("src.zombie_monitor.psutil", create=True)
    def test_with_processes(self, mock_psutil: MagicMock) -> None:
        now = datetime.now()
        mock_proc = MagicMock()
        mock_proc.info = {
            "pid": 1234,
            "name": "git.exe",
            "create_time": now.timestamp() - 7200,
            "cpu_percent": 0.0,
            "memory_info": MagicMock(rss=5 * 1024 * 1024),
        }
        mock_p = MagicMock()
        mock_p.StartTime = now.replace(tzinfo=timezone.utc).replace(tzinfo=None)
        mock_p.MainWindowTitle = ""
        mock_p.CPU = 0.0
        mock_p.WorkingSet64 = 5 * 1024 * 1024
        mock_psutil.process_iter.return_value = [mock_proc]
        mock_psutil.Process.return_value = mock_p

        # psutil may not be installed in test env; skip if import fails
        try:
            result = get_process_zombies()
        except ImportError:
            pytest.skip("psutil not installed")
        assert isinstance(result, list)


class TestGetWorktreeZombies:
    @patch("src.zombie_monitor.subprocess.run")
    def test_empty(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        result = get_worktree_zombies()
        assert result == []


class TestGetStashZombies:
    @patch("src.zombie_monitor.subprocess.run")
    def test_empty(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        result = get_stash_zombies()
        assert result == []


class TestPurgeZombies:
    @patch("src.zombie_monitor.get_process_zombies")
    @patch("src.zombie_monitor.get_worktree_zombies")
    def test_dry_run(self, mock_wt: MagicMock, mock_proc: MagicMock) -> None:
        mock_proc.return_value = []
        mock_wt.return_value = []
        result = purge_zombies(dry_run=True)
        assert result["status"] == "dry_run"
        assert result["wal_logged"] is True
        assert result["purged"] == []

    @patch("src.zombie_monitor.log_wal")
    @patch("src.zombie_monitor.get_process_zombies")
    @patch("src.zombie_monitor.get_worktree_zombies")
    def test_live_purge(self, mock_wt: MagicMock, mock_proc: MagicMock, mock_log: MagicMock) -> None:
        mock_proc.return_value = [
            {
                "pid": 9999,
                "name": "git.exe",
                "type": "git",
                "start_time": datetime.now().isoformat(),
                "age_hours": 2.0,
                "cpu": 0.0,
                "memory_mb": 2.0,
                "main_window_title": "",
            }
        ]
        mock_wt.return_value = []
        result = purge_zombies(types=["git"], dry_run=False)
        assert result["status"] == "purged"
        assert mock_log.called


class TestDetectConflicts:
    def test_empty(self) -> None:
        result = detect_conflicts()
        assert isinstance(result, list)


# ═══════════════════════════════════════════════════════════════════════
# Integration tests — Flask endpoints
# ═══════════════════════════════════════════════════════════════════════

class TestZombieEndpoints:
    def test_list_zombies(self, client: Any) -> None:
        resp = client.get("/health/zombies")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["service"] == "kix"
        assert "process_zombies" in data
        assert "worktree_zombies" in data
        assert "stash_zombies" in data
        assert "summary" in data

    def test_purge_zombies_dry_run(self, client: Any) -> None:
        resp = client.post(
            "/health/zombies/purge",
            data=json.dumps({"types": ["git"], "dry_run": True}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "dry_run"
        assert data["wal_logged"] is True

    def test_purge_zombies_live_blocked_without_types(self, client: Any) -> None:
        # Without types filter, dry_run defaults to True for safety
        resp = client.post(
            "/health/zombies/purge",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "dry_run"

    def test_list_conflicts(self, client: Any) -> None:
        resp = client.get("/health/conflicts")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["service"] == "kix"
        assert "conflicts" in data
        assert "total" in data
