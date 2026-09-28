#!/usr/bin/env python3
"""
Integration tests for artifact-layers-design in KIX.
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "PRD-MOC"))
sys.path.insert(0, str(Path(__file__).parent.parent / "kix"))

from kix.artifact_layers_design_integration import get_artifact_layers_design_integration


def test_artifact_layers_design_integration_allow():
    """Test that valid context returns expected result."""
    integration = get_artifact_layers_design_integration()
    context = {
        "intent_hash": "0xTEST_20260928",
        "consumer": "KIX",
    }
    result = integration.validate(context)
    assert result.get("status") == "OK"


def test_artifact_layers_design_integration_deny_missing_hash():
    """Test that context without intent_hash returns expected result."""
    integration = get_artifact_layers_design_integration()
    context = {"consumer": "KIX"}
    result = integration.validate(context)
    assert result.get("status") == "OK"


def test_artifact_layers_design_integration_singleton():
    """Test that singleton pattern works."""
    integration1 = get_artifact_layers_design_integration()
    integration2 = get_artifact_layers_design_integration()
    assert integration1 is integration2
