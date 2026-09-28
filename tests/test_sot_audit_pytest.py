"""Tests pytest pour l'audit SOT KIX."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from tests.test_sot_audit import audit, CRITICAL_REPOS


class TestSOTAudit:
    def test_gateway_manager_present(self) -> None:
        report = audit()
        gm = next(r for r in report["results"] if r["name"] == "GATEWAY-MANAGER")
        assert gm["status"] == "INCOMPLETE"
        assert gm["runner_type"] == "gateway-exe"
        assert "role" in gm["missing_fields"]

    def test_kix_missing_from_sot(self) -> None:
        report = audit()
        kix = next(r for r in report["results"] if r["name"] == "KIX")
        assert kix["status"] == "INCOMPLETE"
        assert "role" in kix["missing_fields"]

    def test_trix_missing_from_sot(self) -> None:
        report = audit()
        trix = next(r for r in report["results"] if r["name"] == "TRIX")
        assert trix["status"] == "INCOMPLETE"
        assert "role" in trix["missing_fields"]

    def test_flex_missing_from_sot(self) -> None:
        report = audit()
        flex = next(r for r in report["results"] if r["name"] == "FLEX")
        assert flex["status"] == "INCOMPLETE"
        assert "role" in flex["missing_fields"]

    def test_audit_summary_counts(self) -> None:
        report = audit()
        assert report["total_critical"] == 4
        assert report["missing"] == 0
        assert report["incomplete"] == 4
