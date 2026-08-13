"""
Tests pour KIX zombie_monitor.py — validation P0-2.

Vérifie :
- log_kg_l_edge() émet bien des edges KG-L
- purge_zombies() journalise dans WAL et KG-L
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

# Ajouter le chemin KIX/src pour pouvoir importer zombie_monitor
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from src.zombie_monitor import log_kg_l_edge, log_wal, purge_zombies
import src.zombie_monitor as zm


class TestKGLEmission:
    def test_log_kg_l_edge_creates_file(self, tmp_path):
        original_wal_dir = zm.WAL_DIR
        zm.WAL_DIR = tmp_path
        zm.KG_L_EDGE_FILE = tmp_path / "kg-l-edges.jsonl"

        try:
            log_kg_l_edge(
                src="guard:zombie-threshold",
                dst="process:1234",
                kind="prevents",
                metadata={"reason": "zombie"},
            )

            assert zm.KG_L_EDGE_FILE.exists()
            lines = zm.KG_L_EDGE_FILE.read_text(encoding="utf-8").strip().split("\n")
            assert len(lines) == 1
            edge = json.loads(lines[0])
            assert edge["src"] == "guard:zombie-threshold"
            assert edge["dst"] == "process:1234"
            assert edge["kind"] == "prevents"
            assert edge["metadata"]["reason"] == "zombie"
        finally:
            zm.WAL_DIR = original_wal_dir

    def test_log_kg_l_edge_multiple_edges(self, tmp_path):
        original_wal_dir = zm.WAL_DIR
        zm.WAL_DIR = tmp_path
        zm.KG_L_EDGE_FILE = tmp_path / "kg-l-edges.jsonl"

        try:
            log_kg_l_edge(src="a", dst="b", kind="causes")
            log_kg_l_edge(src="b", dst="c", kind="causes")

            lines = zm.KG_L_EDGE_FILE.read_text(encoding="utf-8").strip().split("\n")
            assert len(lines) == 2
        finally:
            zm.WAL_DIR = original_wal_dir


class TestPurgeZombies:
    def test_purge_dry_run_emits_kg_l_edges(self, tmp_path):
        from unittest.mock import patch

        original_wal_dir = zm.WAL_DIR
        zm.WAL_DIR = tmp_path
        zm.KG_L_EDGE_FILE = tmp_path / "kg-l-edges.jsonl"

        fake_zombie = {
            "type": "git",
            "pid": 99999,
            "name": "git.exe",
            "action": "would_stop",
        }

        try:
            with patch("src.zombie_monitor.get_process_zombies", return_value=[fake_zombie]):
                result = purge_zombies(dry_run=True, types=["git"])
            assert result["status"] == "dry_run"
            assert len(result["purged"]) == 1
            # Vérifier que WAL a été écrit
            wal_files = list(tmp_path.glob("*.jsonl"))
            assert len(wal_files) >= 1
        finally:
            zm.WAL_DIR = original_wal_dir
