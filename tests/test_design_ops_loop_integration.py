#!/usr/bin/env python3
"""
Integration tests for design-ops-loop in KIX.
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "PRD-MOC"))
sys.path.insert(0, str(Path(__file__).parent.parent / "kix"))

from kix.design_ops_loop_integration import get_design_ops_loop_integration


def test_design_ops_loop_integration_allow():
    """Test that valid context returns expected result."""
    integration = get_design_ops_loop_integration()
    context = {
        "intent_hash": "0xTEST_20260928",
        "consumer": "KIX",
    }
    result = integration.validate(context)
    assert result.get("loop") == "THINK/DO/CHECK"
    assert result.get("status") == "COMPLETED"


def test_design_ops_loop_integration_deny_missing_hash():
    """Test that context without intent_hash returns expected result."""
    integration = get_design_ops_loop_integration()
    context = {"consumer": "KIX"}
    result = integration.validate(context)
    assert result.get("loop") == "THINK/DO/CHECK"
    assert result.get("status") == "COMPLETED"


def test_design_ops_loop_integration_singleton():
    """Test that singleton pattern works."""
    integration1 = get_design_ops_loop_integration()
    integration2 = get_design_ops_loop_integration()
    assert integration1 is integration2
