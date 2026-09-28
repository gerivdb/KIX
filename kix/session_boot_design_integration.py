#!/usr/bin/env python3
"""
Integration module for session-boot-design design in KIX.
"""

import sys
from pathlib import Path

prd_dir = Path(__file__).parent.parent / "PRD-MOC"
sys.path.insert(0, str(prd_dir))

from session_boot_design import SessionBoot


class SessionBootIntegration:
    """Integration wrapper for session-boot-design."""

    def __init__(self):
        self.session_boot_design = SessionBoot()

    def validate(self, context: dict) -> dict:
        """Validate using session-boot-design."""
        return self.session_boot_design.run_boot_checks(context)

    def check_and_execute(self, context: dict, action_func) -> dict:
        """Check session-boot-design then execute action if allowed."""
        validation = self.validate(context)
        if validation.get("phase") == "BOOT":
            result = action_func(context)
            return {"validation": validation, "execution": result}
        else:
            return {"validation": validation, "execution": None}


_session_boot_design_integration = None


def get_session_boot_design_integration() -> SessionBootIntegration:
    """Get or create singleton instance."""
    global _session_boot_design_integration
    if _session_boot_design_integration is None:
        _session_boot_design_integration = SessionBootIntegration()
    return _session_boot_design_integration
