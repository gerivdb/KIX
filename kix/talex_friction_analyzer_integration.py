#!/usr/bin/env python3
"""
Integration module for talex-friction-analyzer design in KIX.
"""

import sys
from pathlib import Path

prd_dir = Path(__file__).parent.parent / "PRD-MOC"
sys.path.insert(0, str(prd_dir))

from talex_friction_analyzer import TalexFrictionAnalyzer


class TalexFrictionAnalyzerIntegration:
    """Integration wrapper for talex-friction-analyzer."""

    def __init__(self):
        self.talex_friction_analyzer = TalexFrictionAnalyzer()

    def validate(self, context: dict) -> dict:
        """Validate using talex-friction-analyzer."""
        return self.talex_friction_analyzer.analyze(context)

    def check_and_execute(self, context: dict, action_func) -> dict:
        """Check talex-friction-analyzer then execute action if allowed."""
        validation = self.validate(context)
        if validation.get("status") == "OK":
            result = action_func(context)
            return {"validation": validation, "execution": result}
        else:
            return {"validation": validation, "execution": None}


_talex_friction_analyzer_integration = None


def get_talex_friction_analyzer_integration() -> TalexFrictionAnalyzerIntegration:
    """Get or create singleton instance."""
    global _talex_friction_analyzer_integration
    if _talex_friction_analyzer_integration is None:
        _talex_friction_analyzer_integration = TalexFrictionAnalyzerIntegration()
    return _talex_friction_analyzer_integration
