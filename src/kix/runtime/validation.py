"""Validation runtime KG-L.

IntentHash: 0xPRD_MOC_GEN_025_KG_L_GOVERNANCE_WIRING_20260827
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class ValidationResult:
    ok: bool
    issues: List[str] = None

    def __post_init__(self):
        if self.issues is None:
            self.issues = []


def validate_kg_l_runtime(graph_path: Path, registry_path: Path) -> ValidationResult:
    """Valide le graphe KG-L au runtime."""
    issues: List[str] = []

    if not graph_path.exists():
        issues.append(f"missing graph: {graph_path}")
        return ValidationResult(ok=False, issues=issues)

    if not registry_path.exists():
        issues.append(f"missing registry: {registry_path}")
        return ValidationResult(ok=False, issues=issues)

    try:
        import json
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
    except Exception as exc:
        issues.append(f"graph load failed: {exc}")
        return ValidationResult(ok=False, issues=issues)

    nodes = graph.get("nodes", [])
    if not nodes:
        issues.append("graph empty")
        return ValidationResult(ok=False, issues=issues)

    required = ["id", "name", "layer", "status", "local_path", "remote"]
    for node in nodes:
        if not isinstance(node, dict):
            issues.append(f"node is not dict: {node}")
            continue
        if not node.get("local_path"):
            continue
        if node.get("status") != "ACTIVE" or node.get("entity_type") != "REPO":
            continue
        missing = [field for field in required if not node.get(field)]
        if missing:
            issues.append(f"node={node.get('id')} missing={missing}")

    return ValidationResult(ok=len(issues) == 0, issues=issues)
