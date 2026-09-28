#!/usr/bin/env python3
"""
Integration module for talex-friction-analyzer design in KIX.
"""

from pathlib import Path

from kix.pipelines.talex_friction_analyzer import TalexFrictionAnalyzerKix


class TalexFrictionAnalyzer:
    """Compatibility alias."""

    def __init__(self) -> None:
        self._impl = TalexFrictionAnalyzerKix()

    def analyze(self, context: dict) -> dict:
        return self._impl.analyze(context)


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
