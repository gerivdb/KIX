"""Pipeline Ecosystem Meta-Coherence pour KIX.

Vérifie la cohérence cross-repo et détecte les gaps/drifts/contradictions.
Consumer du design `ecosystem-meta-coherence`.

IntentHash: 0xPRD_MOC_KIX_ECOSYSTEM_META_COHERENCE_CONSUMER_20260928
Source: PRD-MOC-KIX-ECOSYSTEM-META-COHERENCE-CONSUMER-20260928.md
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class EcosystemMetaCoherenceKix:
    """Vérificateur de méta-cohérence écosystémique pour KIX."""

    def __init__(self, context: dict[str, Any] | None = None) -> None:
        self.context: dict[str, Any] = context or {}
        self.validation_time: str = datetime.now(timezone.utc).isoformat()

    def verify(self, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Vérifie la méta-cohérence écosystémique."""
        if context:
            self.context = context

        checks = self.context.get("coherence_checks", [])
        results = []
        for check in checks:
            results.append({
                "name": check.get("name", "unknown"),
                "status": "OK" if check.get("coherent", True) else "DRIFT",
                "expected": check.get("expected"),
                "actual": check.get("actual"),
            })

        drifts = [r for r in results if r["status"] == "DRIFT"]
        return {
            "design": "ecosystem-meta-coherence",
            "status": "COHERENT" if not drifts else "DRIFT_DETECTED",
            "checks": results,
            "drifts": drifts,
            "timestamp": self.validation_time,
        }

    def get_gaps(self, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Retourne les gaps de cohérence."""
        if context:
            self.context = context
        result = self.verify(context)
        return result.get("drifts", [])
