"""Watchdog cohérence KG-L.

IntentHash: 0xPRD_MOC_GEN_025_KG_L_GOVERNANCE_WIRING_20260827
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def check_graph(graph_path: Path) -> dict:
    if not graph_path.exists():
        return {"status": "ERROR", "message": f"missing graph: {graph_path}"}

    try:
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"status": "ERROR", "message": f"graph load failed: {exc}"}

    nodes = graph.get("nodes", [])
    if not nodes:
        return {"status": "ERROR", "message": "graph empty"}

    required = ["id", "name", "layer", "status", "local_path", "remote"]
    issues = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        if not node.get("local_path"):
            continue
        if node.get("status") != "ACTIVE" or node.get("entity_type") != "REPO":
            continue
        missing = [field for field in required if not node.get(field)]
        if missing:
            issues.append(f"node={node.get('id')} missing={missing}")

    return {
        "status": "OK" if not issues else "ISSUES",
        "checked": len(nodes),
        "issues": issues,
        "checked_at_utc": _now_utc(),
    }


def run_watchdog(repo_root: Path | None = None) -> int:
    repo_root = repo_root or Path(__file__).resolve().parents[3]
    graph_path = repo_root / "KG-L" / "docs" / "ecosystem_kg_full.json"
    result = check_graph(graph_path)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") == "OK" else 1


if __name__ == "__main__":
    sys.exit(run_watchdog())
