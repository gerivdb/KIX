"""
Garde G-PERIMETER pour KIX ⇄ ENV3.

Règles :
- Les runners KIX ne peuvent écrire que dans les strates L0-L6.
- Aucun accès aux fichiers SOT (known_repositories.yaml, AGENT_RAM.yaml, BRIDGES.yaml).
"""
from __future__ import annotations

import logging
from pathlib import Path

ALLOWED_STRATES = ["L0", "L1", "L2", "L3", "L4", "L5", "L6"]
FORBIDDEN_PATHS = [
    "known_repositories.yaml",
    "AGENT_RAM.yaml",
    "BRIDGES.yaml",
]


class PerimeterGuard:
    """Valide les contraintes G-PERIMETER avant exécution runner."""

    def __init__(self, allowed_strates: list[str] | None = None, forbidden_paths: list[str] | None = None) -> None:
        self.allowed_strates = allowed_strates or ALLOWED_STRATES
        self.forbidden_paths = forbidden_paths or FORBIDDEN_PATHS

    def validate_path(self, path: str | Path) -> None:
        """Valide qu'un chemin est dans les strates autorisées et ne référence pas la SOT."""
        path_str = str(path)
        for forbidden in self.forbidden_paths:
            if forbidden in path_str:
                raise PermissionError(f"G-PERIMETER violation: forbidden path '{forbidden}' referenced")
        normalized = path_str.replace("/", "\\")
        if "TOOLS\\L" in normalized:
            strate_part = normalized.split("TOOLS\\L")[1][:1]
            if strate_part not in self.allowed_strates:
                raise PermissionError(f"G-PERIMETER violation: strate '{strate_part}' not allowed")

    def validate_trits(self, trits: str) -> None:
        """Valide que les trits ne contiennent pas de référence à des chemins interdits."""
        for forbidden in self.forbidden_paths:
            if forbidden in trits:
                raise PermissionError(f"G-PERIMETER violation: forbidden path '{forbidden}' in trits")
