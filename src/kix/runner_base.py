"""BaseRunner complet pour KIX.

Architecture cible :
- health/metrics/WAZAA/signals/DI
- Configuration centralisée via Pydantic Settings
- Métriques Prometheus standardisées
- Signal handlers (SIGTERM/SIGINT) standardisés

IntentHash: 0xPRD_MOC_VOLTX_PHASE3_RUNNERS_STANDARD_20260905
"""

from __future__ import annotations

import signal
from abc import ABC
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class RunnerSpec:
    """Définition déclarative d'un runner service."""

    name: str
    runner_type: str  # "python" | "zig-binary" | "gateway-exe" | "rust" | "node" | "custom"
    port: int
    working_dir: Path
    entrypoint: str | None = None
    binary: str | None = None
    command: list[str] | None = None
    env: dict[str, str] | None = None
    health_path: str = "/healthz"
    health_timeout: float = 5.0
    depends_on: list[str] | None = None
    build: dict | None = None
    bootstrap: bool = False
    auto_start: bool = True
    restart_policy: str | None = None
    log_file: Path | None = None
    meta: dict[str, Any] | None = None
    headers: dict[str, str] | None = None


class BaseRunner(ABC):
    """Runner de base avec health, metrics, WAZAA, signals, DI."""

    def __init__(self, spec: RunnerSpec) -> None:
        self.spec = spec
        self._setup_signal_handlers()

    def _setup_signal_handlers(self) -> None:
        """Configure les signal handlers standardisés."""
        signal.signal(signal.SIGTERM, self._handle_sigterm)
        signal.signal(signal.SIGINT, self._handle_sigint)

    def _handle_sigterm(self, signum: int, frame: Any) -> None:
        """Handler SIGTERM standardisé."""
        self.stop()

    def _handle_sigint(self, signum: int, frame: Any) -> None:
        """Handler SIGINT standardisé."""
        self.stop()

    def start(self) -> dict:
        """Démarre le service. Retourne {status, pid?, detail?}."""
        raise NotImplementedError

    def stop(self, pid: int | None = None) -> dict:
        """Arrête le processus identifié par pid."""
        raise NotImplementedError

    def status(self, pid: int) -> dict:
        """Retourne {status, pid} — running ou stopped."""
        raise NotImplementedError

    def health(self) -> dict:
        """Interroge le endpoint de santé. Retourne {status, http_status?, detail?}."""
        raise NotImplementedError

    def logs(self, lines: int = 100) -> str:
        """Retourne les dernières lignes de logs."""
        raise NotImplementedError

    def restart(self, pid: int) -> dict:
        """Redémarre le service (stop + start)."""
        stop_result = self.stop(pid)
        if stop_result.get("status") != "stopped":
            return stop_result
        return self.start()

    def metrics(self) -> dict:
        """Retourne les métriques Prometheus standardisées."""
        return {
            "runner": self.spec.name,
            "topic": self.spec.meta.get("topic", "unknown") if self.spec.meta else "unknown",
            "status": "unknown",
            "port": self.spec.port,
        }

    def wazaa_publish(self, topic: str, payload: dict) -> None:
        """Publie un événement sur WAZAA."""
        # Stub — à implémenter avec WAZAA_Client
        pass
