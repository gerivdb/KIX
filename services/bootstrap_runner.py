"""Bootstrap Runner - Service d'orchestration du démarrage système KIX.

Port: 8810
Endpoints:
  GET  /health
  GET  /bootstrap/status
  GET  /bootstrap/ready
  POST /bootstrap/start
"""

import os
import sys
import json
import time
import socket
import logging
import keyring
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [BOOTSTRAP] %(message)s")
logger = logging.getLogger("bootstrap")

SERVICE_NAME = "bootstrap"
PORT = 8810

# Dépendances et leurs ports attendus
DEPENDENCIES = {
    "gateway-manager": {"port": 9000, "path": "/health", "required": True},
    "kix": {"port": 8800, "path": "/health", "required": True},
    "arbiter": {"port": 8742, "path": "/health", "required": True},
    "trixd": {"port": 7243, "path": "/health", "required": True},
    "wazaa": {"port": 5002, "path": "/health", "required": True},
    "flex-api": {"port": 8080, "path": "/health", "required": False},
}

# Phases du cycle de vie
PHASE_PENDING = "pending"
PHASE_CHECKING = "checking"
PHASE_STARTING = "starting"
PHASE_READY = "ready"
PHASE_FAILED = "failed"


class BootstrapState:
    def __init__(self) -> None:
        self.status = PHASE_PENDING
        self.phase = PHASE_PENDING
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.services: dict[str, dict[str, Any]] = {}
        self.blockers: list[str] = []
        self.ready: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "phase": self.phase,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services": self.services,
            "ready": self.ready,
            "blockers": self.blockers,
        }


state = BootstrapState()


def check_port(host: str, port: int, timeout: float = 1.0) -> bool:
    """Vérifie si un port est ouvert."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def check_service(name: str, info: dict[str, Any]) -> dict[str, Any]:
    """Vérifie l'état d'un service."""
    host = "127.0.0.1"
    port = info["port"]
    path = info.get("path", "/health")
    required = info.get("required", True)

    status = {
        "status": "unknown",
        "port": port,
        "required": required,
    }

    if check_port(host, port):
        status["status"] = "running"
    else:
        status["status"] = "stopped"
        if required:
            state.blockers.append(f"{name}: port {port} not reachable")

    state.services[name] = status
    return status


def check_all_dependencies() -> bool:
    """Vérifie toutes les dépendances. Retourne True si toutes les requises sont up."""
    state.phase = PHASE_CHECKING
    state.blockers = []

    all_ok = True
    for name, info in DEPENDENCIES.items():
        check_service(name, info)
        if state.services[name]["status"] != "running" and info.get("required", True):
            all_ok = False

    return all_ok


def resolve_secret(var_name: str) -> str | None:
    """Résout un secret depuis l'environnement ou le keyring."""
    # 1. Variables d'environnement
    value = os.environ.get(var_name)
    if value:
        return value

    # 2. Keyring système
    try:
        value = keyring.get_password("gerivdb", var_name.lower())
        if value:
            return value
    except Exception as exc:  # pragma: no cover - défensif
        logger.warning("Keyring lookup failed for %s: %s", var_name, exc)

    return None


class BootstrapHandler(BaseHTTPRequestHandler):
    """Handler HTTP pour le runner bootstrap."""

    server_version = "BootstrapRunner/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        logger.info(fmt, *args)

    def _send_json(self, status_code: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send_json(200, {"status": "ok", "service": SERVICE_NAME})
        elif self.path == "/bootstrap/status":
            check_all_dependencies()
            self._send_json(200, state.to_dict())
        elif self.path == "/bootstrap/ready":
            check_all_dependencies()
            if state.ready and not state.blockers:
                self._send_json(200, state.to_dict())
            else:
                self._send_json(503, state.to_dict())
        else:
            self.send_error(404, "Not Found")

    def do_POST(self) -> None:
        if self.path == "/bootstrap/start":
            if state.phase == PHASE_READY:
                self._send_json(200, {"message": "already ready", "state": state.to_dict()})
                return

            state.phase = PHASE_STARTING
            # TODO: implémenter la séquence de démarrage ordonnée
            # (Arbiter, trixd headers dynamiques, KIXRegistrar, etc.)
            state.phase = PHASE_READY
            state.ready = True
            state.status = "ready"
            self._send_json(202, {"message": "bootstrap started", "state": state.to_dict()})
        else:
            self.send_error(404, "Not Found")


def run() -> None:
    """Démarre le serveur bootstrap."""
    host = "127.0.0.1"
    server = HTTPServer((host, PORT), BootstrapHandler)
    logger.info("Bootstrap runner starting on %s:%d", host, PORT)

    # Check initial au démarrage
    check_all_dependencies()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Bootstrap runner stopped")
        server.shutdown()


if __name__ == "__main__":
    run()
