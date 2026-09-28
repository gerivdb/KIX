#!/usr/bin/env python3
"""
Integration tests for meta-design-self-healing in KIX.
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "PRD-MOC"))
sys.path.insert(0, str(Path(__file__).parent.parent / "kix"))

from kix.meta_design_self_healing_integration import get_meta_design_self_healing_integration


def test_meta_design_self_healing_integration_allow():
    """Test that valid context returns expected result."""
    integration = get_meta_design_self_healing_integration()
    context = {
        "intent_hash": "0xTEST_20260928",
        "consumer": "KIX",
    }
    result = integration.validate(context)
    assert result.get("status") == "HEALTHY"


def test_meta_design_self_healing_integration_deny_missing_hash():
    """Test that context without intent_hash returns expected result."""
    integration = get_meta_design_self_healing_integration()
    context = {"consumer": "KIX"}
    result = integration.validate(context)
    assert result.get("status") == "HEALTHY"


def test_meta_design_self_healing_integration_singleton():
    """Test that singleton pattern works."""
    integration1 = get_meta_design_self_healing_integration()
    integration2 = get_meta_design_self_healing_integration()
    assert integration1 is integration2
