#!/usr/bin/env python3
"""
Integration module for artifact-layers-design design in KIX.
"""

import sys
from pathlib import Path

prd_dir = Path(__file__).parent.parent / "PRD-MOC"
sys.path.insert(0, str(prd_dir))

from artifact_layers_design import ArtifactLayers


class ArtifactLayersIntegration:
    """Integration wrapper for artifact-layers-design."""

    def __init__(self):
        self.artifact_layers_design = ArtifactLayers()

    def validate(self, context: dict) -> dict:
        """Validate using artifact-layers-design."""
        return self.artifact_layers_design.validate(context)

    def check_and_execute(self, context: dict, action_func) -> dict:
        """Check artifact-layers-design then execute action if allowed."""
        validation = self.validate(context)
        if validation.get("status") == "OK":
            result = action_func(context)
            return {"validation": validation, "execution": result}
        else:
            return {"validation": validation, "execution": None}


_artifact_layers_design_integration = None


def get_artifact_layers_design_integration() -> ArtifactLayersIntegration:
    """Get or create singleton instance."""
    global _artifact_layers_design_integration
    if _artifact_layers_design_integration is None:
        _artifact_layers_design_integration = ArtifactLayersIntegration()
    return _artifact_layers_design_integration
