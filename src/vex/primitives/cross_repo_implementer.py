"""Cross-Repo Implementer — Primitive d'implémentation cross-repo atomique pour VEX."""

from __future__ import annotations

from pathlib import Path
from typing import Any


class CrossRepoImplementer:
    """Implémente des changements cross-repo de manière atomique et SLM-compatible.

    Note — portée VEX-native :
        Cette classe est une primitive VEX-native. Elle dépend de concepts VEX
        (VEXRegistry, VEXDaemonManager, chemins PRD-MOC/ADR) et ne doit pas être
        confondue avec une primitive PRIMUS. Si une version générique est nécessaire,
        elle doit être créée dans `gerivdb/PRIMUS` avec son propre PRD-MOC.

    Entrées:
        target_repos: liste des repos cibles
        implementation_plan: plan d'implémentation par repo
        max_files_per_commit: nombre max de fichiers par commit (défaut: 3)

    Sorties:
        Commits atomiques par repo, rapports de validation, preuves d'exécution
    """

    def __init__(
        self,
        target_repos: list[dict[str, Any]],
        implementation_plan: dict[str, Any],
        max_files_per_commit: int = 3,
    ):
        self.target_repos = target_repos
        self.implementation_plan = implementation_plan
        self.max_files_per_commit = max_files_per_commit

    def analyze_scope(self) -> dict[str, Any]:
        """Analyse le scope d'implémentation cross-repo."""
        return {
            "total_repos": len(self.target_repos),
            "total_files": sum(len(r.get("files", [])) for r in self.target_repos),
            "estimated_commits": sum(
                max(1, len(r.get("files", [])) // self.max_files_per_commit)
                for r in self.target_repos
            ),
            "repos": [r["name"] for r in self.target_repos],
        }

    def plan_commits(self, repo: dict[str, Any]) -> list[dict[str, Any]]:
        """Planifie les commits atomiques pour un repo."""
        files = repo.get("files", [])
        commits = []
        for i in range(0, len(files), self.max_files_per_commit):
            batch = files[i : i + self.max_files_per_commit]
            commits.append({
                "repo": repo["name"],
                "path": repo["path"],
                "files": batch,
                "message": f"feat({repo['name']}): {repo.get('slug', 'update')} part {len(commits)+1}",
            })
        return commits

    def validate_repo(self, repo: dict[str, Any]) -> dict[str, Any]:
        """Valide qu'un repo est prêt pour l'implémentation."""
        path = Path(repo["path"])
        return {
            "repo": repo["name"],
            "path": str(path),
            "exists": path.exists(),
            "is_git": (path / ".git").exists(),
            "valid": path.exists() and (path / ".git").exists(),
        }

    def execute_repo(self, repo: dict[str, Any]) -> dict[str, Any]:
        """Exécute l'implémentation pour un repo."""
        validation = self.validate_repo(repo)
        if not validation["valid"]:
            return {
                "repo": repo["name"],
                "status": "skipped",
                "reason": "invalid repo path or not a git repo",
            }

        commits = self.plan_commits(repo)
        return {
            "repo": repo["name"],
            "path": repo["path"],
            "status": "planned",
            "commits": commits,
            "total_commits": len(commits),
        }

    def execute(self) -> dict[str, Any]:
        """Exécute l'implémentation cross-repo complète."""
        result = {
            "scope": self.analyze_scope(),
            "repos": [],
            "total_commits": 0,
        }

        for repo in self.target_repos:
            repo_result = self.execute_repo(repo)
            result["repos"].append(repo_result)
            result["total_commits"] += repo_result.get("total_commits", 0)

        return result
