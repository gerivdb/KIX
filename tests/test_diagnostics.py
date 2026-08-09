"""Tests for KIX diagnostics module."""

import json
import sys
from pathlib import Path

import pytest

# Add src to path
REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from diagnostics import DiagnosticsResult, check_kilocode_cli, check_auth, check_providers, check_runners, run_all_checks


class TestDiagnosticsResult:
    def test_initial_state(self):
        result = DiagnosticsResult("test_check")
        assert result.check == "test_check"
        assert result.status == "OK"
        assert result.detail == ""
        assert "timestamp" in result.to_dict()

    def test_set_error(self):
        result = DiagnosticsResult("test_check")
        result.set_error("Something failed")
        assert result.status == "ERROR"
        assert result.detail == "Something failed"

    def test_set_warn(self):
        result = DiagnosticsResult("test_check")
        result.set_warn("Warning message")
        assert result.status == "WARN"
        assert result.detail == "Warning message"

    def test_to_dict(self):
        result = DiagnosticsResult("test_check")
        result.set_warn("Test warning")
        d = result.to_dict()
        assert d["check"] == "test_check"
        assert d["status"] == "WARN"
        assert d["detail"] == "Test warning"
        assert "timestamp" in d


class TestCheckKilocodeCli:
    def test_kilocode_available(self):
        result = check_kilocode_cli()
        assert result.check == "kilocode_cli"
        # We expect it to be available in the test environment
        # or at least not crash
        assert result.status in ("OK", "ERROR")

    def test_result_has_detail(self):
        result = check_kilocode_cli()
        assert isinstance(result.detail, str)
        assert len(result.detail) > 0


class TestCheckAuth:
    def test_auth_check_runs(self):
        result = check_auth()
        assert result.check == "kilocode_auth"
        assert result.status in ("OK", "ERROR", "WARN")


class TestCheckProviders:
    def test_providers_check_runs(self):
        result = check_providers()
        assert result.check == "providers"
        assert result.status in ("OK", "WARN", "ERROR")

    def test_providers_missing_file(self, monkeypatch, tmp_path):
        # Simulate missing providers file
        monkeypatch.setattr(
            "diagnostics.Path.home",
            lambda: tmp_path,
        )
        result = check_providers()
        assert result.status == "WARN"
        assert "not found" in result.detail.lower()


class TestCheckRunners:
    def test_runners_check_runs(self):
        result = check_runners()
        assert result.check == "kix_runners"
        assert result.status in ("OK", "WARN", "ERROR")


class TestRunAllChecks:
    def test_run_all_checks(self):
        report = run_all_checks()
        assert "timestamp" in report
        assert "total" in report
        assert "ok" in report
        assert "warn" in report
        assert "error" in report
        assert "checks" in report
        assert report["total"] == 4
        assert len(report["checks"]) == 4

    def test_checks_have_required_fields(self):
        report = run_all_checks()
        for check in report["checks"]:
            assert "check" in check
            assert "status" in check
            assert "detail" in check
            assert "timestamp" in check
            assert check["status"] in ("OK", "WARN", "ERROR")
