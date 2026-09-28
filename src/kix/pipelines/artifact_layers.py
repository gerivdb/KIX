"""Pipeline Artifact Layers Design pour KIX.

Valide le respect des couches d'artefacts : core, adapter, presentation.
Consumer du design `artifact-layers-design`.

IntentHash: 0xPRD_MOC_KIX_ARTIFACT_LAYERS_DESIGN_CONSUMER_20260928
Source: PRD-MOC-KIX-ARTIFACT-LAYERS-DESIGN-CONSUMER-20260928.md
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class ArtifactLayersKix:
    """Validateur des couches d'artefacts pour KIX."""

    def __init__(self, context: dict[str, Any] | None = None) -> None:
        self.context: dict[str, Any] = context or {}
        self.validation_time: str = datetime.now(timezone.utc).isoformat()

    def validate(self, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Valide les couches d'artefacts."""
        if context:
            self.context = context

        artifacts = self.context.get("artifacts", [])
        valid_layers = {"core", "adapter", "presentation"}
        results = []
        for artifact in artifacts:
            layer = artifact.get("layer", "")
            results.append({
                "name": artifact.get("name", "unknown"),
                "layer": layer,
                "valid": layer in valid_layers,
            })

        all_valid = all(r["valid"] for r in results)
        return {
            "design": "artifact-layers-design",
            "status": "VALID" if all_valid else "INVALID",
            "results": results,
            "timestamp": self.validation_time,
        }

    def get_violations(self, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Retourne les violations de couches."""
        if context:
            self.context = context
        result = self.validate(context)
        return [r for r in result["results"] if not r["valid"]]
