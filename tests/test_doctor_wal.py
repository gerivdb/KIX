"""Tests pour le module WAL doctor."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from doctor_wal import create_backup, get_wal_entries, log_wal, restore_backup, WAL_FILE


class TestDoctorWAL:
    def test_log_wal_creates_file(self, tmp_path: Path) -> None:
        test_wal = tmp_path / "test-doctor.jsonl"
        with patch("doctor_wal.WAL_FILE", test_wal):
            log_wal("test_event", {"key": "value"})
        assert test_wal.exists()
        with open(test_wal, "r", encoding="utf-8") as f:
            line = f.readline()
        record = json.loads(line)
        assert record["event_type"] == "test_event"
        assert record["data"]["key"] == "value"
        assert "timestamp" in record

    def test_create_backup(self, tmp_path: Path) -> None:
        src = tmp_path / "config.yaml"
        src.write_text("key: value")
        test_wal = tmp_path / "test-doctor.jsonl"
        with patch("doctor_wal.WAL_FILE", test_wal):
            backup = create_backup(src)
        assert backup is not None
        assert backup.exists()
        assert backup.read_text() == "key: value"
        assert backup.name == "config.yaml.bak"

    def test_create_backup_missing_source(self, tmp_path: Path) -> None:
        src = tmp_path / "nonexistent.yaml"
        backup = create_backup(src)
        assert backup is None

    def test_restore_backup(self, tmp_path: Path) -> None:
        src = tmp_path / "config.yaml"
        src.write_text("original")
        backup = src.with_suffix(".yaml.bak")
        backup.write_text("backup_content")
        test_wal = tmp_path / "test-doctor.jsonl"
        with patch("doctor_wal.WAL_FILE", test_wal):
            result = restore_backup(src)
        assert result is True
        assert src.read_text() == "backup_content"

    def test_restore_backup_missing(self, tmp_path: Path) -> None:
        src = tmp_path / "config.yaml"
        src.write_text("original")
        result = restore_backup(src)
        assert result is False

    def test_get_wal_entries(self, tmp_path: Path) -> None:
        test_wal = tmp_path / "test-doctor.jsonl"
        entries_data = [
            {"event_type": "backup_created", "data": {"source": "/a"}},
            {"event_type": "restart", "data": {"name": "svc"}},
            {"event_type": "backup_created", "data": {"source": "/b"}},
        ]
        with open(test_wal, "w", encoding="utf-8") as f:
            for entry in entries_data:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        with patch("doctor_wal.WAL_FILE", test_wal):
            all_entries = get_wal_entries()
            assert len(all_entries) == 3
            backup_entries = get_wal_entries(event_type="backup_created")
            assert len(backup_entries) == 2
