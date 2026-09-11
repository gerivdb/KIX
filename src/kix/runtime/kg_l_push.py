"""Producer KG-L : Mnemo -> KG-L push.

IntentHash: 0xPRD_MOC_GEN_025_KG_L_GOVERNANCE_WIRING_20260827
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def push_from_mnemo(payload: dict[str, Any], graph_path: Path | None = None) -> int:
    graph_path = graph_path or Path(__file__).resolve().parents[1] / "KG-L" / "docs" / "ecosystem_kg_full.json"
    if not graph_path.exists():
        print(f"[KG-L-PUSH] missing graph: {graph_path}")
        return 1
    data = json.loads(graph_path.read_text(encoding="utf-8"))
    data.setdefault("meta", {})["last_push_from_mnemo_utc"] = (
        __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
    )
    graph_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("[KG-L-PUSH] pushed from mnemo")
    return 0


if __name__ == "__main__":
    sys.exit(push_from_mnemo({}))
