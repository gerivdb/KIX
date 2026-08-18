"""Interface contractuelle et base abstraite pour tous les runners KIX."""

from __future__ import annotations

from abc import ABC, abstractmethod
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


class RunnerBase(ABC):
    """Interface minimale que tout wrapper runner doit implémenter."""

    def __init__(self, spec: RunnerSpec) -> None:
        self.spec = spec

    @abstractmethod
    def start(self) -> dict:
        """Démarre le service. Retourne {status, pid?, detail?}."""

    @abstractmethod
    def stop(self, pid: int) -> dict:
        """Arrête le processus identifié par pid."""

    @abstractmethod
    def status(self, pid: int) -> dict:
        """Retourne {status, pid} — running ou stopped."""

    @abstractmethod
    def health(self) -> dict:
        """Interroge le endpoint de santé. Retourne {status, http_status?, detail?}."""

    @abstractmethod
    def logs(self, lines: int = 100) -> str:
        """Retourne les dernières lignes de logs."""

    @abstractmethod
    def restart(self, pid: int) -> dict:
        """Redémarre le service (stop + start)."""
