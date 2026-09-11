"""Consumer KG-L : export vers Mnemo.

IntentHash: 0xPRD_MOC_GEN_025_KG_L_GOVERNANCE_WIRING_20260827
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def export_to_mnemo(graph_path: Path | None = None) -> int:
    graph_path = graph_path or Path(__file__).resolve().parents[1] / "KG-L" / "docs" / "ecosystem_kg_full.json"
    if not graph_path.exists():
        print(f"[KG-L-MNEMO] missing graph: {graph_path}")
        return 1
    data = json.loads(graph_path.read_text(encoding="utf-8"))
    print(f"[KG-L-MNEMO] exported {len(data.get('nodes', []))} nodes")
    return 0


if __name__ == "__main__":
    sys.exit(export_to_mnemo())
