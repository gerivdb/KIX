#!/usr/bin/env python3
"""
Governance Hub Client — Client REST/YAML pour GOVERNANCE-HUB (L0-CANON).

Intégration KIX × GOVERNANCE-HUB pour agréger les registres et valider
les documents de gouvernance (ADR, PRD-MOC, INTENT).

Protocole : REST + YAML parsing
Endpoint : http://localhost:8801 (ou chemin local vers known_repositories.yaml)
Timeout : 5s (configurable)
"""

from __future__ import annotations

import json
import logging
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any, Optional

import yaml

logger = logging.getLogger("kix.governance_hub_client")

GOV_HUB_HEALTH = "http://localhost:8801/health"
GOV_HUB_REGISTRY = "http://localhost:8801/registry"
KNOWN_REPOSITORIES_PATH = Path(__file__).resolve().parents[2] / "GOVERNANCE-HUB" / "known_repositories.yaml"


class GovernanceHubError(Exception):
    """Erreur du client GOVERNANCE-HUB."""


class GovernanceHubClient:
    """Client REST/YAML pour GOVERNANCE-HUB."""

    def __init__(
        self,
        base_url: str = GOV_HUB_REGISTRY,
        local_path: Optional[Path] = None,
        timeout: int = 5,
    ) -> None:
        self.base_url = base_url
        self.local_path = local_path or KNOWN_REPOSITORIES_PATH
        self.timeout = timeout

    def _get(self, endpoint: str) -> dict[str, Any]:
        """Effectue un appel GET."""
        req = urllib.request.Request(f"{self.base_url}{endpoint}", method="GET")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise GovernanceHubError(f"GOVERNANCE-HUB unreachable: {exc}") from exc
        except TimeoutError:
            raise GovernanceHubError(f"GOVERNANCE-HUB timeout after {self.timeout}s")

    def _post(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Effectue un appel POST."""
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}{endpoint}",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise GovernanceHubError(f"GOVERNANCE-HUB unreachable: {exc}") from exc
        except TimeoutError:
            raise GovernanceHubError(f"GOVERNANCE-HUB timeout after {self.timeout}s")

    def get_registry(self, registry_name: str) -> dict[str, Any]:
        """Récupère un registre YAML (local ou remote)."""
        if self.local_path.exists():
            with open(self.local_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if registry_name in data:
                return data[registry_name]
            raise GovernanceHubError(f"Registry '{registry_name}' not found in {self.local_path}")
        return self._get(f"/registry/{registry_name}")

    def validate_adr(self, adr_path: str) -> bool:
        """Valide un ADR (frontmatter + structure)."""
        payload = {"path": adr_path}
        result = self._post("/validate/adr", payload)
        return result.get("valid", False)

    def validate_prd_moc(self, path: str) -> bool:
        """Valide un PRD-MOC (frontmatter + structure)."""
        payload = {"path": path}
        result = self._post("/validate/prd-moc", payload)
        return result.get("valid", False)

    def health(self) -> dict[str, Any]:
        """Vérifie la santé du service."""
        if self.local_path.exists():
            return {"status": "ok", "mode": "local", "path": str(self.local_path)}
        try:
            return self._get("/health")
        except GovernanceHubError:
            return {"status": "unreachable", "mode": "remote"}
