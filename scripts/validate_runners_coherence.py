"""Validation cohérence runners.yaml <-> KG-L.

IntentHash: 0xPRD_MOC_GEN_025_KG_L_GOVERNANCE_WIRING_20260827
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml


def _load_registry_ids(registry_path: Path) -> set[str]:
    try:
        registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[KG-L-RUNNERS] registry load failed: {exc}")
        return set()

    ids = set()
    for repo in registry.get("P0_REPOS", registry.get("repositories", [])):
        name = repo.get("name")
        if name:
            ids.add(name)
    return ids


def validate() -> int:
    root = Path(__file__).resolve().parents[1]
    runners_path = root / "config" / "runners.yaml"
    registry_path = root.parents[1] / "L0-CANON" / "GOVERNANCE-HUB" / "known_repositories.yaml"

    if not runners_path.exists():
        print("[KG-L-RUNNERS] missing runners.yaml")
        return 1

    if not registry_path.exists():
        print("[KG-L-RUNNERS] missing registry")
        return 1

    try:
        runners = yaml.safe_load(runners_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[KG-L-RUNNERS] runners load failed: {exc}")
        return 1

    known_ids = _load_registry_ids(registry_path)
    if not known_ids:
        print("[KG-L-RUNNERS] empty registry")
        return 1

    issues = []
    warnings = []
    for runner in runners.get("runners", []):
        for dep in runner.get("depends_on", []):
            if dep in known_ids:
                continue
            warnings.append(f"runner={runner.get('id')} unknown dep={dep}")

    if warnings:
        for warning in warnings:
            print(f"[KG-L-RUNNERS] WARN {warning}")

    if issues:
        for issue in issues:
            print(f"[KG-L-RUNNERS] ISSUE {issue}")
        return 1

    print("[KG-L-RUNNERS] coherence OK")
    return 0


if __name__ == "__main__":
    sys.exit(validate())
