#!/usr/bin/env python3
r"""
Test SessionBootKix (PRD-MOC-KIX-SESSION-BOOT-DESIGN-CONSUMER-20260928)
"""
import io
import sys

# ERR_030 FIX
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from kix.pipelines.session_boot import SessionBootKix


def test_run_boot_checks_completes():
    """run_boot_checks returns COMPLETED with checks."""
    boot = SessionBootKix(context={
        "boot_checks": [
            {"name": "env_check"},
            {"name": "dependency_check"},
        ]
    })
    result = boot.run_boot_checks()

    assert result["phase"] == "BOOT"
    assert result["status"] == "COMPLETED"
    assert len(result["checks"]) == 2
    assert "timestamp" in result


def test_run_closeout_checks_completes():
    """run_closeout_checks returns COMPLETED with checks."""
    boot = SessionBootKix(context={
        "closeout_checks": [
            {"name": "branch_cleanup"},
            {"name": "working_tree_clean"},
        ]
    })
    result = boot.run_closeout_checks()

    assert result["phase"] == "CLOSEOUT"
    assert result["status"] == "COMPLETED"
    assert len(result["checks"]) == 2
    assert "timestamp" in result


def test_run_boot_checks_empty():
    """run_boot_checks handles empty checks list."""
    boot = SessionBootKix()
    result = boot.run_boot_checks()

    assert result["status"] == "COMPLETED"
    assert result["checks"] == []


def test_run_closeout_checks_empty():
    """run_closeout_checks handles empty checks list."""
    boot = SessionBootKix()
    result = boot.run_closeout_checks()

    assert result["status"] == "COMPLETED"
    assert result["checks"] == []


def test_run_boot_checks_timestamp_utc():
    """run_boot_checks includes ISO UTC timestamp."""
    boot = SessionBootKix()
    result = boot.run_boot_checks()

    assert "timestamp" in result
    assert result["timestamp"].endswith("+00:00") or result["timestamp"].endswith("Z")


def test_run_closeout_checks_timestamp_utc():
    """run_closeout_checks includes ISO UTC timestamp."""
    boot = SessionBootKix()
    result = boot.run_closeout_checks()

    assert "timestamp" in result
    assert result["timestamp"].endswith("+00:00") or result["timestamp"].endswith("Z")
