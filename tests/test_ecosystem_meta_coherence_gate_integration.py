#!/usr/bin/env python3
"""
Integration tests for ecosystem-meta-coherence-gate in KIX.
"""

import pytest
from pathlib import Path
import sys

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "PRD-MOC"))
sys.path.insert(0, str(Path(__file__).parent.parent / "kix"))

from kix.ecosystem_meta_coherence_gate_integration import get_ecosystem_meta_coherence_gate_integration


def test_ecosystem_meta_coherence_gate_integration_allow():
    """Test that valid context is allowed."""
    integration = get_ecosystem_meta_coherence_gate_integration()
    context = {
        "intent_hash": "0xTEST_20260928",
        "consumer": "KIX",
    }
    result = integration.validate(context)
    assert result.get("state") == "ALLOW"


def test_ecosystem_meta_coherence_gate_integration_deny_missing_hash():
    """Test that context without intent_hash is denied."""
    integration = get_ecosystem_meta_coherence_gate_integration()
    context = {"consumer": "KIX"}
    result = integration.validate(context)
    assert result.get("state") == "DENY"


def test_ecosystem_meta_coherence_gate_integration_singleton():
    """Test that singleton pattern works."""
    integration1 = get_ecosystem_meta_coherence_gate_integration()
    integration2 = get_ecosystem_meta_coherence_gate_integration()
    assert integration1 is integration2
