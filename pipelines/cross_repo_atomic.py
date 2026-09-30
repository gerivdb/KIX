#!/usr/bin/env python3
"""Cross-Repo Atomic Pipeline — Pattern d'implémentation atomique pour CTULU."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOTS = {
    "N243": Path("D:/DO/WEB/TOOLS/L4-TOOLS/N243"),
    "KIX": Path("D:/DO/WEB/TOOLS/L2-PLATFORM/KIX"),
    "CTULU": Path("D:/DO/WEB/TOOLS/L4-TOOLS/CTULU"),
    "BRAIN": Path("D:/DO/WEB/TOOLS/L0-CANON/BRAIN"),
}


def validate_artifact(source: Path, destination: Path) -> dict[str, Any]:
    """Valide et déploie un artifact atomiquement."""
    if not source.exists():
        return {"status": "skipped", "reason": f"source not found: {source}"}

    if destination.exists():
        existing = destination.read_text(encoding="utf-8", errors="ignore")
        new_content = source.read_text(encoding="utf-8")
        if existing.strip() == new_content.strip():
            return {"status": "noop", "reason": "destination already up-to-date"}

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(source.read_bytes())
    return {"status": "deployed", "source": str(source), "destination": str(destination)}


def _normalize_artifacts(artifacts: list | dict) -> list[dict[str, str]]:
    if isinstance(artifacts, dict) and "required" in artifacts:
        return [{"source": item, "destination": item} for item in artifacts["required"]]
    return artifacts


def deploy_to_repo(repo_name: str, repo_root: Path, artifacts: list[dict[str, str]]) -> dict[str, Any]:
    """Déploie une liste d'artifacts vers un repo cible."""
    if not repo_root.exists():
        return {"repo": repo_name, "status": "error", "reason": f"repo not found: {repo_root}"}

    normalized = _normalize_artifacts(artifacts)
    results = []
    for artifact in normalized:
        source = Path(artifact["source"])
        destination = repo_root / artifact["destination"]
        result = validate_artifact(source, destination)
        result.setdefault("repo", repo_name)
        results.append(result)

    return {
        "repo": repo_name,
        "status": "ok",
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="CTULU Cross-Repo Atomic Pipeline")
    parser.add_argument("--artifacts", type=Path, required=True, help="Chemin vers le JSON des artifacts à déployer")
    parser.add_argument("--repos", default="N243,KIX,CTULU,BRAIN", help="Repos cibles séparés par des virgules")
    parser.add_argument("--output", type=Path, default=None, help="Chemin de sortie pour le rapport JSON")
    parser.add_argument("--dry-run", action="store_true", help="Simulation sans écriture")
    args = parser.parse_args()

    if not args.artifacts.exists():
        raise SystemExit(f"Artifacts file not found: {args.artifacts}")

    artifacts = json.loads(args.artifacts.read_text(encoding="utf-8"))
    repo_names = [name.strip() for name in args.repos.split(",") if name.strip()]

    report = {
        "deployed_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "dry_run": args.dry_run,
        "repos": [],
    }

    for repo_name in repo_names:
        repo_root = REPO_ROOTS.get(repo_name)
        if repo_root is None:
            report["repos"].append({
                "repo": repo_name,
                "status": "skipped",
                "reason": "unknown repo name",
            })
            continue
        if args.dry_run:
            report["repos"].append({
                "repo": repo_name,
                "status": "dry-run",
                "root": str(repo_root),
            })
        else:
            report["repos"].append(deploy_to_repo(repo_name, repo_root, artifacts))

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Deployment report written to {args.output}")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
