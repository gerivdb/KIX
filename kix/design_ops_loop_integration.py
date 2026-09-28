#!/usr/bin/env python3
"""
Integration module for design-ops-loop design in KIX.
"""

import sys
from pathlib import Path

prd_dir = Path(__file__).parent.parent / "PRD-MOC"
sys.path.insert(0, str(prd_dir))

from design_ops_loop import DesignOpsLoop


class DesignOpsLoopIntegration:
    """Integration wrapper for design-ops-loop."""

    def __init__(self):
        self.design_ops_loop = DesignOpsLoop()

    def validate(self, context: dict) -> dict:
        """Validate using design-ops-loop."""
        return self.design_ops_loop.run(context)

    def check_and_execute(self, context: dict, action_func) -> dict:
        """Check design-ops-loop then execute action if allowed."""
        validation = self.validate(context)
        if validation.get("status") == "COMPLETED":
            result = action_func(context)
            return {"validation": validation, "execution": result}
        else:
            return {"validation": validation, "execution": None}


_design_ops_loop_integration = None


def get_design_ops_loop_integration() -> DesignOpsLoopIntegration:
    """Get or create singleton instance."""
    global _design_ops_loop_integration
    if _design_ops_loop_integration is None:
        _design_ops_loop_integration = DesignOpsLoopIntegration()
    return _design_ops_loop_integration
