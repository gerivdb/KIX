#!/usr/bin/env python3
"""
Integration module for safe-action-pattern design in KIX.
Wraps the standalone implementation for use in KIX commands.
"""

import sys
from pathlib import Path

# Add PRD directory to path for imports
prd_dir = Path(__file__).parent.parent / "PRD-MOC"
sys.path.insert(0, str(prd_dir))

from safe_action_pattern import SafeActionGate, run_safe_action


class SafeActionGateIntegration:
    """Integration wrapper for safe-action-pattern."""

    def __init__(self):
        self.safe_action_pattern = SafeActionGate()

    def validate(self, context: dict) -> dict:
        """Validate using safe-action-pattern."""
        return self.safe_action_pattern.verify(context)

    def check_and_execute(self, context: dict, action_func) -> dict:
        """Check safe-action-pattern then execute action if allowed."""
        validation = self.validate(context)
        if validation.get("state") == "ALLOW":
            result = action_func(context)
            return {"validation": validation, "execution": result}
        else:
            return {"validation": validation, "execution": None}


# Singleton
_safe_action_pattern_integration = None


def get_safe_action_pattern_integration() -> SafeActionGateIntegration:
    """Get or create singleton instance."""
    global _safe_action_pattern_integration
    if _safe_action_pattern_integration is None:
        _safe_action_pattern_integration = SafeActionGateIntegration()
    return _safe_action_pattern_integration
