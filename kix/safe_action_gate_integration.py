#!/usr/bin/env python3
"""
Integration module for safe-action-gate design in KIX.
Wraps the standalone implementation for use in KIX commands.
"""

import sys
from pathlib import Path

# Add PRD directory to path for imports
prd_dir = Path(__file__).parent.parent / "PRD-MOC"
sys.path.insert(0, str(prd_dir))

from safe_action_gate import SafeActionGate, verify_safe_action_gate


class SafeActionGateIntegration:
    """Integration wrapper for safe-action-gate."""

    def __init__(self):
        self.safe_action_gate = SafeActionGate()

    def validate(self, context: dict) -> dict:
        """Validate using safe-action-gate."""
        return self.safe_action_gate.verify(context)

    def check_and_execute(self, context: dict, action_func) -> dict:
        """Check safe-action-gate then execute action if allowed."""
        validation = self.validate(context)
        if validation.get("state") == "ALLOW":
            result = action_func(context)
            return {"validation": validation, "execution": result}
        else:
            return {"validation": validation, "execution": None}


# Singleton
_safe_action_gate_integration = None


def get_safe_action_gate_integration() -> SafeActionGateIntegration:
    """Get or create singleton instance."""
    global _safe_action_gate_integration
    if _safe_action_gate_integration is None:
        _safe_action_gate_integration = SafeActionGateIntegration()
    return _safe_action_gate_integration
