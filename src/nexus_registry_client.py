#!/usr/bin/env python3
"""
Nexus Registry Client — Client NEXUS pour accès au méga-SOT (L0-CANON).

Intégration KIX × NEXUS pour accéder au registre des registres et
valider la conformité des repos.

Protocole : NEXUS registry protocol (REST/JSON)
Endpoint : http://localhost:8801
Timeout : 5s (configurable)
"""

from __future__ import annotations

import json
import logging
import urllib.request
import urllib.error
from typing import Any, Optional

logger = logging.getLogger("kix.nexus_client")

NEXUS_HEALTH = "http://localhost:8801/health"
NEXUS_REGISTRY = "http://localhost:8801/registry"
NEXUS_REPOS = "http://localhost:8801/repos"


class NexusRegistryError(Exception):
    """Erreur du client NEXUS."""


class NexusRegistryClient:
    """Client NEXUS pour accès au méga-SOT."""

    def __init__(self, base_url: str = NEXUS_REGISTRY, timeout: int = 5) -> None:
        self.base_url = base_url
        self.timeout = timeout

    def _get(self, endpoint: str) -> dict[str, Any]:
        """Effectue un appel GET."""
        req = urllib.request.Request(f"{self.base_url}{endpoint}", method="GET")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise NexusRegistryError(f"NEXUS unreachable: {exc}") from exc
        except TimeoutError:
            raise NexusRegistryError(f"NEXUS timeout after {self.timeout}s")

    def get_registry(self, registry_name: str) -> dict[str, Any]:
        """Récupère un registre NEXUS."""
        result = self._get(f"/{registry_name}")
        logger.info("Retrieved NEXUS registry %s", registry_name)
        return result

    def list_repos(self) -> list[dict[str, Any]]:
        """Liste tous les repos connus."""
        result = self._get("/repos")
        repos = result.get("repos", [])
        logger.info("Listed %d NEXUS repos", len(repos))
        return repos

    def get_repo(self, repo_name: str) -> dict[str, Any]:
        """Récupère un repo par nom."""
        result = self._get(f"/repos/{repo_name}")
        logger.info("Retrieved NEXUS repo %s", repo_name)
        return result

    def health(self) -> dict[str, Any]:
        """Vérifie la santé du service."""
        try:
            return self._get("/health")
        except NexusRegistryError:
            return {"status": "unreachable"}
        except Exception as exc:
            return {"status": "unreachable", "error": str(exc)}
