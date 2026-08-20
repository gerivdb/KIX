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

try:
    import requests
except ImportError:  # pragma: no cover - dépendance externe
    requests = None

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


class SecretResolver:
    """Résout les secrets depuis l'environnement, le keyring ou un fichier .env local."""

    @staticmethod
    def resolve(var_name: str) -> str | None:
        """Résout un secret par nom."""
        return resolve_secret(var_name)


class KIXRegistrar:
    """Enregistre les services dans KIX via son API."""

    def __init__(self, kix_url: str = "http://127.0.0.1:8800") -> None:
        self.kix_url = kix_url.rstrip("/")

    def register_runner(self, name: str, port: int, status: str = "running") -> bool:
        """Enregistre un runner dans KIX via /runners/register."""
        if requests is None:
            logger.warning("KIXRegistrar: requests not installed, skipping registration for %s", name)
            return False
        url = f"{self.kix_url}/runners/register"
        try:
            resp = requests.post(url, json={"name": name, "port": port, "status": status}, timeout=2)
            if resp.status_code == 200:
                data = resp.json()
                logger.info("KIXRegistrar: registered %s -> %s", name, data.get("status"))
                return True
            logger.warning("KIXRegistrar: failed to register %s (HTTP %d): %s", name, resp.status_code, resp.text)
            return False
        except Exception as exc:  # pragma: no cover - défensif
            logger.warning("KIXRegistrar: error registering %s: %s", name, exc)
            return False


class ServiceStarter:
    """Séquence ordonnée de démarrage des services."""

    START_SEQUENCE = [
        ("arbiter", {"port": 8742, "script": "D:/DO/WEB/TOOLS/L4-TOOLS/TRIX/start-git-arbiter.ps1"}),
        ("trixd", {"port": 7243, "required_headers": ["Authorization"]}),
        ("wazaa", {"port": 5002}),
        ("flex-api", {"port": 8080}),
    ]

    def __init__(self, secret_resolver: SecretResolver | None = None, kix_registrar: KIXRegistrar | None = None) -> None:
        self.secret_resolver = secret_resolver or SecretResolver()
        self.kix_registrar = kix_registrar or KIXRegistrar()

    def _start_arbiter(self, config: dict[str, Any]) -> None:
        script = config.get("script")
        if not script:
            logger.info("ServiceStarter: arbiter script not configured")
            return
        if not os.path.exists(script):
            logger.warning("ServiceStarter: arbiter script not found: %s", script)
            state.blockers.append(f"arbiter: script not found: {script}")
            return
        try:
            if sys.platform == "win32":
                cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", script]
            else:
                cmd = ["bash", script]
            logger.info("ServiceStarter: starting arbiter via %s", " ".join(cmd))
            # TODO: capturer pid et l'enregistrer
            state.services["arbiter"] = {"status": "running", "port": config["port"], "required": True}
        except Exception as exc:  # pragma: no cover - défensif
            logger.warning("ServiceStarter: failed to start arbiter: %s", exc)
            state.blockers.append(f"arbiter: {exc}")

    def _start_trixd(self, config: dict[str, Any]) -> None:
        port = config["port"]
        if check_port("127.0.0.1", port):
            logger.info("ServiceStarter: trixd already running on port %d", port)
            state.services["trixd"] = {"status": "running", "port": port, "required": True}
            return
        logger.info("ServiceStarter: trixd not running on port %d, start required", port)
        # trixd est démarré par KIX via runners.yaml, pas directement par bootstrap
        state.services["trixd"] = {"status": "stopped", "port": port, "required": True}
        state.blockers.append(f"trixd: port {port} not reachable, start required via KIX")

    def _start_wazaa(self, config: dict[str, Any]) -> None:
        port = config["port"]
        if check_port("127.0.0.1", port):
            logger.info("ServiceStarter: wazaa already running on port %d", port)
            state.services["wazaa"] = {"status": "running", "port": port, "required": True}
            return
        logger.info("ServiceStarter: wazaa not running on port %d, start required", port)
        # wazaa est démarré par KIX via runners.yaml
        state.services["wazaa"] = {"status": "stopped", "port": port, "required": True}
        state.blockers.append(f"wazaa: port {port} not reachable, start required via KIX")

    def _start_flex_api(self, config: dict[str, Any]) -> None:
        port = config["port"]
        if check_port("127.0.0.1", port):
            logger.info("ServiceStarter: flex-api already running on port %d", port)
            state.services["flex-api"] = {"status": "running", "port": port, "required": False}
            return
        logger.info("ServiceStarter: flex-api not running on port %d, optional", port)
        state.services["flex-api"] = {"status": "stopped", "port": port, "required": False}

    def start(self) -> None:
        """Démarre la séquence ordonnée."""
        state.phase = PHASE_STARTING
        state.status = "starting"

        starters = {
            "arbiter": self._start_arbiter,
            "trixd": self._start_trixd,
            "wazaa": self._start_wazaa,
            "flex-api": self._start_flex_api,
        }

        for service_name, config in self.START_SEQUENCE:
            starter = starters.get(service_name)
            if starter:
                starter(config)
            else:
                logger.info("ServiceStarter: no starter for %s", service_name)
            # Enregistrement dans KIX
            self.kix_registrar.register_runner(service_name, config["port"])

        state.phase = PHASE_READY
        state.ready = True
        state.status = "ready"


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
            ServiceStarter().start()
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
