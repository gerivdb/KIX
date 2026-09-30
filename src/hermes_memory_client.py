#!/usr/bin/env python3
"""
Hermes Memory Client — Client REST/WAZAA pour HERMES/Mnemo (L1-INFRA).

Intégration KIX × HERMES pour lire/écrire dans Mnemo et recevoir des
skills recommandés via WAZAA bus.

Protocole : REST + WAZAA bus
Endpoint : http://localhost:8802
Timeout : 5s (configurable)
"""

from __future__ import annotations

import json
import logging
import urllib.request
import urllib.error
from typing import Any, Optional

logger = logging.getLogger("kix.hermes_client")

HERMES_HEALTH = "http://localhost:8802/health"
HERMES_MEMORY = "http://localhost:8802/memory"
HERMES_SKILLS = "http://localhost:8802/skills"
HERMES_FACTS = "http://localhost:8802/facts"


class HermesMemoryError(Exception):
    """Erreur du client HERMES."""


class HermesMemoryClient:
    """Client REST/WAZAA pour HERMES/Mnemo."""

    def __init__(self, base_url: str = HERMES_MEMORY, timeout: int = 5) -> None:
        self.base_url = base_url
        self.timeout = timeout

    def _get(self, endpoint: str) -> dict[str, Any]:
        """Effectue un appel GET."""
        req = urllib.request.Request(f"{self.base_url}{endpoint}", method="GET")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise HermesMemoryError(f"HERMES unreachable: {exc}") from exc
        except TimeoutError:
            raise HermesMemoryError(f"HERMES timeout after {self.timeout}s")

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
            raise HermesMemoryError(f"HERMES unreachable: {exc}") from exc
        except TimeoutError:
            raise HermesMemoryError(f"HERMES timeout after {self.timeout}s")

    def read_memory(self, key: str) -> dict[str, Any]:
        """Lit une entrée Mnemo."""
        result = self._get(f"/{key}")
        logger.info("Read Mnemo key=%s: %s", key, result.get("value"))
        return result

    def write_memory(self, key: str, value: dict[str, Any]) -> bool:
        """Écrit dans Mnemo."""
        payload = {"key": key, "value": value}
        result = self._post("/write", payload)
        logger.info("Wrote Mnemo key=%s: %s", key, result.get("status"))
        return result.get("status") == "ok"

    def get_recommended_skills(self) -> list[str]:
        """Récupère les skills recommandés."""
        result = self._get("/recommended-skills")
        skills = result.get("skills", [])
        logger.info("Recommended skills: %s", skills)
        return skills

    def publish_fact(self, fact: dict[str, Any]) -> bool:
        """Publie un fait vérifié."""
        payload = {"fact": fact}
        result = self._post("/facts", payload)
        logger.info("Published fact: %s", result.get("id"))
        return result.get("status") == "published"

    def health(self) -> dict[str, Any]:
        """Vérifie la santé du service."""
        try:
            return self._get("/health")
        except HermesMemoryError:
            return {"status": "unreachable"}
        except Exception as exc:
            return {"status": "unreachable", "error": str(exc)}
