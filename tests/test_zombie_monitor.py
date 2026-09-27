"""Tests unitaires pour le zombie monitor intelligent."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.zombie_monitor import get_process_zombies, _ZOMBIE_PROCESS_NAMES


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
