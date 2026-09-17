"""Bootstrap KG-L runtime pour KIX.

IntentHash: 0xPRD_MOC_GEN_025_KG_L_GOVERNANCE_WIRING_20260827
"""

from __future__ import annotations

import sys
from pathlib import Path

from src.kix.runtime.validation import validate_kg_l_runtime


def bootstrap_kg_l() -> int:
    root = Path(__file__).resolve().parents[3]
    graph_path = root / "KG-L" / "docs" / "ecosystem_kg_full.json"
    registry_path = root.parents[1] / "L0-CANON" / "GOVERNANCE-HUB" / "known_repositories.yaml"

    result = validate_kg_l_runtime(graph_path, registry_path)
    if not result.ok:
        for issue in result.issues:
            print(f"[KG-L-BOOT] ISSUE {issue}")
        return 1

    print("[KG-L-BOOT] runtime validation OK")
    return 0


if __name__ == "__main__":
    sys.exit(bootstrap_kg_l())
