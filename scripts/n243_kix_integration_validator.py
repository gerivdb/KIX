#!/usr/bin/env python3
"""N243/KIX Integration Validator — Valide l'intégration des artifacts CTULU dans N243 et KIX."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def validate_repo_integration(repo_path: Path, required_artifacts: list[str]) -> dict[str, Any]:
    """Valide qu'un repo contient les artifacts requis."""
    if not repo_path.exists():
        return {
            "repo": repo_path.name,
            "status": "error",
            "reason": f"repo not found: {repo_path}",
        }

    results = []
    for artifact in required_artifacts:
        artifact_path = repo_path / artifact
        results.append({
            "artifact": artifact,
            "present": artifact_path.exists(),
        })

    present_count = sum(1 for r in results if r["present"])
    return {
        "repo": repo_path.name,
        "status": "ok" if present_count == len(required_artifacts) else "incomplete",
        "present": present_count,
        "total": len(required_artifacts),
        "missing": [r["artifact"] for r in results if not r["present"]],
        "artifacts": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="CTULU N243/KIX Integration Validator")
    parser.add_argument("--n243-path", type=Path, required=True, help="Chemin vers N243")
    parser.add_argument("--kix-path", type=Path, required=True, help="Chemin vers KIX")
    parser.add_argument("--artifacts", type=Path, required=True, help="Chemin vers le JSON des artifacts requis")
    parser.add_argument("--output", type=Path, default=None, help="Chemin de sortie pour le rapport JSON")
    args = parser.parse_args()

    if not args.artifacts.exists():
        raise SystemExit(f"Artifacts file not found: {args.artifacts}")

    artifacts = json.loads(args.artifacts.read_text(encoding="utf-8"))
    required = artifacts.get("required", [])

    n243_result = validate_repo_integration(args.n243_path, required)
    kix_result = validate_repo_integration(args.kix_path, required)

    report = {
        "generated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "n243": n243_result,
        "kix": kix_result,
        "summary": {
            "n243_status": n243_result.get("status"),
            "kix_status": kix_result.get("status"),
            "n243_present": n243_result.get("present", 0),
            "kix_present": kix_result.get("present", 0),
            "total_required": len(required),
        },
    }

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Integration validation report written to {args.output}")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
