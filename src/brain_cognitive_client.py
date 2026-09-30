#!/usr/bin/env python3
"""
Brain Cognitive Client — Client JSON-RPC 2.0 pour BRAIN (L0-CANON).

Intégration KIX × BRAIN pour déclencher des agents cognitifs et recevoir
des résultats via JSON-RPC 2.0 over HTTP.

Protocole : JSON-RPC 2.0
Endpoint : http://localhost:8800
Timeout : 5s (configurable)
"""

from __future__ import annotations

import json
import logging
import urllib.request
import urllib.error
from typing import Any, Optional

logger = logging.getLogger("kix.brain_client")

BRAIN_HEALTH = "http://localhost:8800/health"
BRAIN_RPC = "http://localhost:8800/rpc"


class BrainCognitiveError(Exception):
    """Erreur du client BRAIN."""


class BrainCognitiveClient:
    """Client JSON-RPC 2.0 pour BRAIN."""

    def __init__(self, base_url: str = BRAIN_RPC, timeout: int = 5) -> None:
        self.base_url = base_url
        self.timeout = timeout

    def _rpc_call(self, method: str, params: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Effectue un appel JSON-RPC 2.0."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or {},
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.base_url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                if "error" in body:
                    raise BrainCognitiveError(body["error"])
                return body.get("result", {})
        except urllib.error.URLError as exc:
            raise BrainCognitiveError(f"BRAIN unreachable: {exc}") from exc
        except TimeoutError as exc:
            raise BrainCognitiveError(f"BRAIN timeout after {self.timeout}s") from exc

    def trigger_agent(self, agent_name: str, context: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Déclenche un agent cognitif BRAIN."""
        params = {"agent": agent_name, "context": context or {}}
        result = self._rpc_call("agent.trigger", params)
        logger.info("Triggered BRAIN agent %s: %s", agent_name, result.get("task_id"))
        return result

    def get_result(self, task_id: str) -> dict[str, Any]:
        """Récupère le résultat d'une tâche BRAIN."""
        result = self._rpc_call("task.get", {"task_id": task_id})
        logger.info("Retrieved BRAIN task %s: %s", task_id, result.get("status"))
        return result

    def health(self) -> dict[str, Any]:
        """Vérifie la santé du service BRAIN."""
        req = urllib.request.Request(BRAIN_HEALTH, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            return {"status": "unreachable", "error": str(exc)}
        except TimeoutError:
            return {"status": "timeout", "error": f"timeout after {self.timeout}s"}
        except Exception as exc:
            return {"status": "unreachable", "error": str(exc)}
