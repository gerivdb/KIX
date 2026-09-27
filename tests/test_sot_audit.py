"""Audit de cohérence SOT pour KIX.

Vérifie que les repos critiques orchestrés par KIX sont présents dans
`GOVERNANCE-HUB/known_repositories.yaml` avec les champs attendus.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

SOT_PATH = Path(
    r"D:\DO\WEB\TOOLS\L0-CANON\GOVERNANCE-HUB\known_repositories.yaml"
)

CRITICAL_REPOS = [
    {"name": "KIX", "expected_role": "orchestrator", "expected_runner_type": "python", "expected_port": 8800},
    {"name": "TRIX", "expected_role": "zig-runtime", "expected_runner_type": "zig-binary", "expected_port": 7243},
    {"name": "FLEX", "expected_role": "cache", "expected_runner_type": "rust", "expected_port": 7718},
    {"name": "GATEWAY-MANAGER", "expected_role": "gateway", "expected_runner_type": "gateway-exe", "expected_port": 18000},
]


def load_sot() -> dict[str, Any]:
    with open(SOT_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def audit() -> dict[str, Any]:
    data = load_sot()
    repos = data.get("P0_REPOS", [])
    by_name = {r.get("name"): r for r in repos}

    results = []
    for crit in CRITICAL_REPOS:
        name = crit["name"]
        entry = by_name.get(name)
        if entry is None:
            results.append({
                "name": name,
                "status": "MISSING",
                "expected_role": crit["expected_role"],
                "expected_runner_type": crit["expected_runner_type"],
                "expected_port": crit["expected_port"],
            })
            continue
        missing_fields = []
        for field in ["runner_type", "port", "role", "binary_target"]:
            if field not in entry:
                missing_fields.append(field)
        results.append({
            "name": name,
            "status": "PRESENT" if not missing_fields else "INCOMPLETE",
            "missing_fields": missing_fields,
            "runner_type": entry.get("runner_type"),
            "port": entry.get("port"),
            "role": entry.get("role"),
        })

    return {
        "sot_path": str(SOT_PATH),
        "total_critical": len(CRITICAL_REPOS),
        "missing": sum(1 for r in results if r["status"] == "MISSING"),
        "incomplete": sum(1 for r in results if r["status"] == "INCOMPLETE"),
        "results": results,
    }


if __name__ == "__main__":
    report = audit()
    print(json.dumps(report, ensure_ascii=False, indent=2))
