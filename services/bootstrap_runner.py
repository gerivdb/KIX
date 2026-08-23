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
import subprocess
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

# Dépendances et leurs ports attendus.
# G1 (PRD-MOC-GEN-002) : le bus WAZAA réel écoute 1873 (WazaaBusAsync /
# PORT_ASYNC dans wazaa_bus.py), pas 5002. Rôles distincts :
#   - wazaa         : bus KG-L async TCP (1873), requis
#   - wazaa-threads : bus threadé (8200, PORT_THREADS), même processus
#                     bus_runner.py -> informatif, non bloquant
#   - wazaa-mc      : mission control HTTP (5002), optionnel
DEPENDENCIES = {
    "gateway-manager": {"port": 9000, "path": "/health", "required": True},
    "kix": {"port": 8800, "path": "/health", "required": True},
    "arbiter": {"port": 8742, "path": "/health", "required": True},
    "trixd": {"port": 7243, "path": "/health", "required": True},
    "wazaa": {"port": 1873, "path": None, "protocol": "tcp", "required": True},
    "wazaa-threads": {"port": 8200, "path": None, "protocol": "tcp", "required": False},
    "wazaa-mc": {"port": 5002, "path": "/healthz", "required": False},
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
    """Vérifie toutes les dépendances et met à jour l'état global.

    Sémantique ready (PRD-MOC-GEN-002 §7.4) : si toutes les dépendances
    requises sont joignables, le bootstrap se déclare prêt, même sans
    appel explicite à /bootstrap/start (auto-guérison : des services
    démarrés par un autre chemin publient quand même /bootstrap/ready).
    """
    state.phase = PHASE_CHECKING
    state.blockers = []

    all_ok = True
    for name, info in DEPENDENCIES.items():
        check_service(name, info)
        if state.services[name]["status"] != "running" and info.get("required", True):
            all_ok = False

    if all_ok:
        state.ready = True
        state.status = PHASE_READY
        state.phase = "operational"
    else:
        state.ready = False
        if state.status == PHASE_READY:
            state.status = "degraded"

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


def wait_for_port(port: int, attempts: int = 6, delay: float = 1.0) -> bool:
    """Attend qu'un port local devienne joignable (retry avec backoff léger)."""
    for attempt in range(attempts):
        if check_port("127.0.0.1", port, timeout=1.0):
            return True
        time.sleep(delay * (attempt + 1))
    return check_port("127.0.0.1", port, timeout=1.0)


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


class BootstrapMonitor:
    """Surveille l'état de bootstrap et génère des alertes en cas d'échec."""

    def __init__(self, check_interval: int = 30) -> None:
        self.check_interval = check_interval
        self.alert_count = 0
        self.last_alert: str | None = None

    def check(self) -> dict[str, Any]:
        """Vérifie l'état de bootstrap et génère des alertes si nécessaire."""
        check_all_dependencies()
        alert = None

        if state.phase == PHASE_FAILED:
            alert = "bootstrap failed"
        elif state.blockers:
            alert = f"bootstrap blockers: {', '.join(state.blockers)}"
        elif not state.ready and state.phase != PHASE_PENDING:
            alert = "bootstrap not ready"

        if alert:
            self.alert_count += 1
            self.last_alert = alert
            logger.warning("[MONITOR] ALERTE: %s (count=%d)", alert, self.alert_count)
        else:
            if self.alert_count > 0:
                logger.info("[MONITOR] Retour a la normale apres %d alerte(s)", self.alert_count)
            self.alert_count = 0
            self.last_alert = None

        return {
            "alert": alert,
            "alert_count": self.alert_count,
            "last_alert": self.last_alert,
            "phase": state.phase,
            "ready": state.ready,
            "blockers": state.blockers,
        }


class ServiceStarter:
    """Séquence ordonnée de démarrage des services.

    G3 (PRD-MOC-GEN-002) : l'Arbiter (8742) est démarré par le bootstrap
    via start-git-arbiter.ps1 — plus jamais de démarrage purement manuel.
    Le bus WAZAA réel (1873) est démarré directement via bus_runner.py.
    """

    WAZAA_DIR = "D:/DO/WEB/TOOLS/L4-TOOLS/WAZAA"

    # (clé_etat, config) — kix_runner = nom du runner dans KIX config/runners.yaml
    START_SEQUENCE = [
        ("arbiter", {"port": 8742, "script": "D:/DO/WEB/TOOLS/L4-TOOLS/TRIX/start-git-arbiter.ps1"}),
        ("wazaa", {"port": 1873}),  # bus async réel, démarré en direct
        ("trixd", {"port": 7243, "kix_runner": "trixd"}),
        ("wazaa-mc", {"port": 5002, "kix_runner": "wazaa"}),
        ("flex-api", {"port": 8080, "kix_runner": "flex-api"}),
    ]

    def __init__(self, secret_resolver: SecretResolver | None = None, kix_registrar: KIXRegistrar | None = None) -> None:
        self.secret_resolver = secret_resolver or SecretResolver()
        self.kix_registrar = kix_registrar or KIXRegistrar()

    def _spawn_detached(self, cmd: list[str], cwd: str | None, log_path: str | None = None) -> int:
        """Lance un processus détaché et retourne son pid."""
        kwargs: dict[str, Any] = {
            "cwd": cwd,
            "creationflags": getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        }
        if log_path:
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            log_fh = open(log_path, "a", encoding="utf-8")
            kwargs["stdout"] = log_fh
            kwargs["stderr"] = log_fh
        proc = subprocess.Popen(cmd, **kwargs)
        return proc.pid

    def _start_arbiter(self, key: str, config: dict[str, Any]) -> None:
        port = config["port"]
        state.services[key] = {"status": "starting", "port": port, "required": True}
        if check_port("127.0.0.1", port):
            logger.info("ServiceStarter: arbiter already running on port %d", port)
            state.services[key] = {"status": "running", "port": port, "required": True}
            return
        script = config.get("script")
        if not script or not os.path.exists(script):
            msg = f"arbiter: script not found: {script}"
            logger.warning("ServiceStarter: %s", msg)
            state.blockers.append(msg)
            state.services[key] = {"status": "stopped", "port": port, "required": True}
            return
        try:
            # Wrapper CMD obligatoire (règle harmonisation-v8 §9.1)
            cmd = ["cmd", "/c", "powershell", "-ExecutionPolicy", "ByPass", "-File", script]
            logger.info("ServiceStarter: starting arbiter via %s", " ".join(cmd))
            pid = self._spawn_detached(cmd, cwd=os.path.dirname(script))
            logger.info("ServiceStarter: arbiter spawned pid=%d, waiting for port %d", pid, port)
            if wait_for_port(port):
                state.services[key] = {"status": "running", "port": port, "required": True, "pid": pid}
                logger.info("ServiceStarter: arbiter UP on port %d", port)
            else:
                state.blockers.append(f"arbiter: port {port} still down after start attempt")
                state.services[key] = {"status": "stopped", "port": port, "required": True, "pid": pid}
        except Exception as exc:  # pragma: no cover - défensif
            logger.warning("ServiceStarter: failed to start arbiter: %s", exc)
            state.blockers.append(f"arbiter: {exc}")
            state.services[key] = {"status": "stopped", "port": port, "required": True}

    def _start_wazaa_bus(self, key: str, config: dict[str, Any]) -> None:
        """Démarre le bus WAZAA réel (1873 async + 8200 threads) via bus_runner.py."""
        port = config["port"]
        state.services[key] = {"status": "starting", "port": port, "required": True}
        if check_port("127.0.0.1", port):
            logger.info("ServiceStarter: wazaa bus already running on port %d", port)
            state.services[key] = {"status": "running", "port": port, "required": True}
            return
        entrypoint = os.path.join(self.WAZAA_DIR, "src", "bus_runner.py")
        if not os.path.exists(entrypoint):
            msg = f"wazaa: bus_runner entrypoint not found: {entrypoint}"
            logger.warning("ServiceStarter: %s", msg)
            state.blockers.append(msg)
            state.services[key] = {"status": "stopped", "port": port, "required": True}
            return
        try:
            log_path = os.path.join(self.WAZAA_DIR, "data", "wazaa_bus_bootstrap.log")
            pid = self._spawn_detached([sys.executable, entrypoint], cwd=self.WAZAA_DIR, log_path=log_path)
            logger.info("ServiceStarter: wazaa bus spawned pid=%d, waiting for port %d", pid, port)
            if wait_for_port(port):
                state.services[key] = {"status": "running", "port": port, "required": True, "pid": pid}
                logger.info("ServiceStarter: wazaa bus UP on port %d", port)
            else:
                state.blockers.append(f"wazaa: bus port {port} still down after start attempt")
                state.services[key] = {"status": "stopped", "port": port, "required": True, "pid": pid}
        except Exception as exc:  # pragma: no cover - défensif
            logger.warning("ServiceStarter: failed to start wazaa bus: %s", exc)
            state.blockers.append(f"wazaa: {exc}")
            state.services[key] = {"status": "stopped", "port": port, "required": True}

    def _start_via_kix_runner(self, key: str, config: dict[str, Any]) -> None:
        """Vérifie un runner ; s'il est down tente un démarrage via l'API KIX."""
        port = config["port"]
        required = DEPENDENCIES.get(key, {}).get("required", True)
        state.services[key] = {"status": "starting", "port": port, "required": required}
        if check_port("127.0.0.1", port):
            logger.info("ServiceStarter: %s already running on port %d", key, port)
            state.services[key] = {"status": "running", "port": port, "required": required}
            return
        kix_name = config.get("kix_runner", key)
        logger.info("ServiceStarter: %s not running on port %d, starting via KIX (%s)", key, port, kix_name)
        started = self._start_via_kix(kix_name)
        if started and wait_for_port(port, attempts=3, delay=1.0):
            state.services[key] = {"status": "running", "port": port, "required": required}
        elif not started:
            # KIX auto_start (Phase 2 de src/app.py) prendra le relais si KIX
            # n'était pas encore joignable : pas un blocker définitif ici,
            # le check final fera foi.
            logger.info("ServiceStarter: %s deferred to KIX auto_start", key)
            state.services[key] = {"status": "unknown", "port": port, "required": required}

    def _start_via_kix(self, name: str, timeout: int = 10) -> bool:
        """Démarre un runner via KIX POST /runners/<name>/start (canal interne)."""
        if requests is None:
            logger.warning("ServiceStarter: requests not installed, cannot start %s via KIX", name)
            return False
        url = f"{self.kix_registrar.kix_url}/runners/{name}/start"
        try:
            resp = requests.post(
                url,
                headers={"X-KIX-Bootstrap": "1"},
                timeout=timeout,
            )
            if resp.status_code == 200:
                data = resp.json()
                logger.info("ServiceStarter: %s started via KIX -> %s", name, data.get("status"))
                return True
            logger.warning("ServiceStarter: failed to start %s via KIX (HTTP %d): %s", name, resp.status_code, resp.text)
            return False
        except Exception as exc:  # pragma: no cover - défensif
            logger.warning("ServiceStarter: error starting %s via KIX: %s", name, exc)
            return False

    def start(self) -> None:
        """Démarre la séquence ordonnée puis re-checke l'état réel (autoritaire)."""
        state.phase = PHASE_STARTING
        state.status = "starting"

        starters = {
            "arbiter": self._start_arbiter,
            "wazaa": self._start_wazaa_bus,
            "trixd": self._start_via_kix_runner,
            "wazaa-mc": self._start_via_kix_runner,
            "flex-api": self._start_via_kix_runner,
        }

        for service_key, config in self.START_SEQUENCE:
            starter = starters.get(service_key)
            if starter:
                starter(service_key, config)
            else:
                logger.info("ServiceStarter: no starter for %s", service_key)
            # Enregistrement dans KIX (nom KIX si défini, sinon la clé d'état)
            kix_name = config.get("kix_runner", service_key)
            self.kix_registrar.register_runner(kix_name, config["port"])

        # Laisse respirer les services fraîchement démarrés, puis état final.
        time.sleep(2.0)
        all_ok = check_all_dependencies()
        logger.info(
            "ServiceStarter: sequence done -> status=%s ready=%s blockers=%s",
            state.status,
            state.ready,
            state.blockers,
        )
        if not all_ok:
            state.status = "degraded"


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
        elif self.path == "/bootstrap/monitor":
            monitor = BootstrapMonitor()
            report = monitor.check()
            code = 200 if report.get("alert") is None else 503
            self._send_json(code, report)
        else:
            self.send_error(404, "Not Found")

    def do_POST(self) -> None:
        if self.path == "/bootstrap/start":
            if state.ready and not state.blockers:
                self._send_json(200, {"message": "already ready", "state": state.to_dict()})
                return

            ServiceStarter().start()
            # start() a déjà re-checké les dépendances et fixé status/ready.
            self._send_json(202, {"message": "bootstrap sequence executed", "state": state.to_dict()})
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
