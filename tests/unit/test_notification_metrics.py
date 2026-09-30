"""Tests for src/notification_metrics.py."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from src.notification_metrics import NotificationMetrics, NotificationMetricsStore


class TestNotificationMetrics:
    def test_create_default(self):
        metrics = NotificationMetrics(channel="email")
        assert metrics.channel == "email"
        assert metrics.total_sent == 0

    def test_create_with_values(self):
        metrics = NotificationMetrics(channel="email", total_sent=5, total_success=4, total_failed=1, avg_latency_ms=120.5)
        assert metrics.total_sent == 5
        assert metrics.total_success == 4
        assert metrics.total_failed == 1
        assert metrics.avg_latency_ms == 120.5


class TestNotificationMetricsStore:
    def test_record_send_insert(self, tmp_path):
        db = tmp_path / "metrics.db"
        store = NotificationMetricsStore(db)
        store.record_send("email", success=True, latency_ms=100.0)
        all_metrics = store.list_all()
        assert len(all_metrics) == 1
        assert all_metrics["email"].total_sent == 1
        assert all_metrics["email"].total_success == 1
        assert all_metrics["email"].total_failed == 0

    def test_record_send_update(self, tmp_path):
        db = tmp_path / "metrics.db"
        store = NotificationMetricsStore(db)
        store.record_send("email", success=True, latency_ms=100.0)
        store.record_send("email", success=False, latency_ms=200.0)
        all_metrics = store.list_all()
        assert all_metrics["email"].total_sent == 2
        assert all_metrics["email"].total_success == 1
        assert all_metrics["email"].total_failed == 1

    def test_list_all_empty(self, tmp_path):
        db = tmp_path / "metrics.db"
        store = NotificationMetricsStore(db)
        all_metrics = store.list_all()
        assert all_metrics == {}
