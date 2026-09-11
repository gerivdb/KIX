"""Consumer KG-L : analyse spectrale ClusterWave.

IntentHash: 0xPRD_MOC_GEN_025_KG_L_GOVERNANCE_WIRING_20260827
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def analyze_spectral(graph_path: Path | None = None) -> dict[str, Any]:
    graph_path = graph_path or Path(__file__).resolve().parents[1] / "KG-L" / "docs" / "ecosystem_kg_full.json"
    if not graph_path.exists():
        return {"status": "ERROR", "detail": f"missing graph: {graph_path}"}
    data = json.loads(graph_path.read_text(encoding="utf-8"))
    return {
        "status": "OK",
        "nodes": len(data.get("nodes", [])),
        "checked_at_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    result = analyze_spectral()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result.get("status") == "OK" else 1)
