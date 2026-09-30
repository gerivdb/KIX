"""Tests for src/auto_remediation.py."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from src.auto_remediation import RemediationResult, RemediationStore


class TestRemediationResult:
    def test_create_default(self):
        result = RemediationResult(
            policy_id="POL-001",
            service="KIX",
            action_type="restart",
            success=True,
            detail="Restarted successfully",
            timestamp="2026-09-30T23:00:00+00:00",
        )
        assert result.policy_id == "POL-001"
        assert result.service == "KIX"
        assert result.action_type == "restart"
        assert result.success is True
        assert result.detail == "Restarted successfully"
        assert result.timestamp == "2026-09-30T23:00:00+00:00"

    def test_create_with_none_service(self):
        result = RemediationResult(
            policy_id="POL-002",
            service=None,
            action_type="backoff",
            success=False,
            detail="Backoff applied",
            timestamp="2026-09-30T23:00:00+00:00",
        )
        assert result.service is None
        assert result.success is False


class TestRemediationStore:
    def test_init_creates_schema(self, tmp_path):
        db = tmp_path / "remediation.db"
        store = RemediationStore(db)
        assert db.exists()

    def test_record_remediation(self, tmp_path):
        db = tmp_path / "remediation.db"
        store = RemediationStore(db)
        result = RemediationResult(
            policy_id="POL-001",
            service="KIX",
            action_type="restart",
            success=True,
            detail="Restarted",
            timestamp="2026-09-30T23:00:00+00:00",
        )
        record_id = store.record(result)
        assert record_id == 1

    def test_list_recent_empty(self, tmp_path):
        db = tmp_path / "remediation.db"
        store = RemediationStore(db)
        records = store.list_recent()
        assert records == []

    def test_list_recent_with_records(self, tmp_path):
        db = tmp_path / "remediation.db"
        store = RemediationStore(db)
        for i in range(3):
            result = RemediationResult(
                policy_id=f"POL-{i:03d}",
                service="KIX",
                action_type="restart",
                success=True,
                detail=f"Action {i}",
                timestamp=f"2026-09-30T23:{i:02d}:00+00:00",
            )
            store.record(result)
        records = store.list_recent(limit=2)
        assert len(records) == 2
        assert records[0]["policy_id"] == "POL-002"
        assert records[1]["policy_id"] == "POL-001"

    def test_record_with_failure(self, tmp_path):
        db = tmp_path / "remediation.db"
        store = RemediationStore(db)
        result = RemediationResult(
            policy_id="POL-001",
            service="KIX",
            action_type="restart",
            success=False,
            detail="Failed to restart",
            timestamp="2026-09-30T23:00:00+00:00",
        )
        record_id = store.record(result)
        assert record_id == 1
        records = store.list_recent()
        assert len(records) == 1
        assert records[0]["success"] == 0
