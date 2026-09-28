#!/usr/bin/env python3
"""
Integration tests for safe-action-pattern in KIX.
"""

import pytest
from pathlib import Path
import sys

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "PRD-MOC"))
sys.path.insert(0, str(Path(__file__).parent.parent / "kix"))

from kix.safe_action_pattern_integration import get_safe_action_pattern_integration


def test_safe_action_pattern_integration_allow():
    """Test that valid context is allowed."""
    integration = get_safe_action_pattern_integration()
    context = {
        "intent_hash": "0xTEST_20260928",
        "consumer": "KIX",
    }
    result = integration.validate(context)
    assert result.get("state") == "ALLOW"


def test_safe_action_pattern_integration_deny_missing_hash():
    """Test that context without intent_hash is denied."""
    integration = get_safe_action_pattern_integration()
    context = {"consumer": "KIX"}
    result = integration.validate(context)
    assert result.get("state") == "DENY"


def test_safe_action_pattern_integration_singleton():
    """Test that singleton pattern works."""
    integration1 = get_safe_action_pattern_integration()
    integration2 = get_safe_action_pattern_integration()
    assert integration1 is integration2
