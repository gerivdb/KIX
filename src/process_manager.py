"""Process Manager — PID registry, singleton bind, fingerprint.

Couvre P0 du PRD-MOC GEN-041 :
- PIDRegistry : inventaire canonique des processus autorisés
- SingletonBindManager : preflight avant bind + fingerprint /health
- ProcessManager : façade pour KIX
"""

from __future__ import annotations

import json
import logging
import os
import socket
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import requests

logger = logging.getLogger("kix.process")

# ---------------------------------------------------------------------------
# Modèles
# ---------------------------------------------------------------------------

@dataclass
class ProcessEntry:
    pid: int
    name: str
    repo: str
    role: str
    port: int
    started_at: str
    last_seen: str
    fingerprint: str
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pid": self.pid,
            "name": self.name,
            "repo": self.repo,
            "role": self.role,
            "port": self.port,
            "started_at": self.started_at,
            "last_seen": self.last_seen,
            "fingerprint": self.fingerprint,
            "meta": self.meta,
        }


@dataclass
class SingletonCheckResult:
    ok: bool
    action: str
    existing_pid: Optional[int] = None
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "action": self.action,
            "existing_pid": self.existing_pid,
            "message": self.message,
        }


# ---------------------------------------------------------------------------
# PID Registry
# ---------------------------------------------------------------------------

class PIDRegistry:
    """Inventaire canonique des processus autorisés (in-memory + JSON file)."""

    def __init__(self, state_file: Path | None = None) -> None:
        self._entries: dict[int, ProcessEntry] = {}
        self._state_file = state_file or Path(
            os.environ.get("KIX_PID_REGISTRY", "data/pid_registry.json")
        )
        self._load()

    def register(self, entry: ProcessEntry) -> None:
        self._entries[entry.pid] = entry
        self._save()

    def unregister(self, pid: int) -> None:
        self._entries.pop(pid, None)
        self._save()

    def get(self, pid: int) -> Optional[ProcessEntry]:
        return self._entries.get(pid)

    def list_all(self) -> list[ProcessEntry]:
        return list(self._entries.values())

    def find_by_port(self, port: int) -> Optional[ProcessEntry]:
        for entry in self._entries.values():
            if entry.port == port:
                return entry
        return None

    def find_by_name(self, name: str) -> list[ProcessEntry]:
        return [e for e in self._entries.values() if e.name == name]

    def prune_dead(self) -> list[int]:
        dead: list[int] = []
        for pid, entry in list(self._entries.items()):
            if not _is_process_alive(pid):
                dead.append(pid)
                self._save()
        return dead

    def _save(self) -> None:
        try:
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._state_file, "w", encoding="utf-8") as f:
                json.dump(
                    [e.to_dict() for e in self._entries.values()],
                    f,
                    indent=2,
                    default=str,
                )
        except Exception as exc:
            logger.warning("PIDRegistry save failed: %s", exc)

    def _load(self) -> None:
        if not self._state_file.exists():
            return
        try:
            with open(self._state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data:
                entry = ProcessEntry(
                    pid=int(item["pid"]),
                    name=str(item["name"]),
                    repo=str(item.get("repo", "")),
                    role=str(item.get("role", "")),
                    port=int(item.get("port", 0)),
                    started_at=str(item.get("started_at", "")),
                    last_seen=str(item.get("last_seen", "")),
                    fingerprint=str(item.get("fingerprint", "")),
                    meta=item.get("meta", {}),
                )
                self._entries[entry.pid] = entry
        except Exception as exc:
            logger.warning("PIDRegistry load failed: %s", exc)


# ---------------------------------------------------------------------------
# Singleton Bind Manager
# ---------------------------------------------------------------------------

class SingletonBindManager:
    """Preflight singleton avant bind + fingerprint d'instance."""

    def __init__(self, registry: PIDRegistry) -> None:
        self._registry = registry

    def preflight(self, port: int, service_name: str, expected_fingerprint: str | None = None) -> SingletonCheckResult:
        """Vérifie qu'aucun homonyme n'écoute déjà sur ce port.

        Retourne SingletonCheckResult(ok=True/False, action=bloque|warn|ok, ...).
        """
        # 1. Vérifier dans le registry local
        existing = self._registry.find_by_port(port)
        if existing is not None and _is_process_alive(existing.pid):
            # Fingerprint mismatch : warn (instance existante mais fingerprint différent)
            if expected_fingerprint and existing.fingerprint and existing.fingerprint != expected_fingerprint:
                msg = (
                    f"[PREFLIGHT] WARN: fingerprint mismatch sur {service_name}:"
                    f" attendu={expected_fingerprint}, trouve={existing.fingerprint}"
                )
                logger.warning(msg)
                return SingletonCheckResult(
                    ok=False,
                    action="warn",
                    existing_pid=existing.pid,
                    message=msg,
                )
            msg = (
                f"[PREFLIGHT] FATAL: instance {service_name} DEJA ACTIVE sur 127.0.0.1:{port} "
                f"(pid={existing.pid}, fingerprint={existing.fingerprint})"
            )
            logger.warning(msg)
            return SingletonCheckResult(
                ok=False,
                action="bloque",
                existing_pid=existing.pid,
                message=msg,
            )

        # 2. Vérifier via socket si quelque chose écoute
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1.0):
                msg = f"[PREFLIGHT] FATAL: port {port} déjà utilisé (socket connectable)"
                logger.warning(msg)
                return SingletonCheckResult(ok=False, action="bloque", message=msg)
        except (OSError, ConnectionRefusedError, socket.timeout):
            pass

        # 3. Si fingerprint attendu, vérifier la cohérence
        if expected_fingerprint and existing is not None:
            if existing.fingerprint != expected_fingerprint:
                msg = (
                    f"[PREFLIGHT] WARN: fingerprint mismatch sur {service_name}:"
                    f" attendu={expected_fingerprint}, trouve={existing.fingerprint}"
                )
                logger.warning(msg)
                return SingletonCheckResult(ok=False, action="warn", existing_pid=existing.pid, message=msg)

        return SingletonCheckResult(ok=True, action="ok", message="Singleton preflight OK")

    @staticmethod
    def probe_fingerprint(port: int, health_path: str = "/healthz", timeout: float = 2.0) -> Optional[str]:
        """Interroge /health et retourne le champ `build` comme fingerprint."""
        try:
            url = f"http://127.0.0.1:{port}{health_path}"
            resp = requests.get(url, timeout=timeout)
            if resp.status_code == 200:
                data = resp.json()
                return str(data.get("build", ""))
        except Exception:
            pass
        return None


# ---------------------------------------------------------------------------
# Process Manager (façade KIX)
# ---------------------------------------------------------------------------

class ProcessManager:
    """Façade KIX pour la gestion système des processus."""

    def __init__(self, registry: PIDRegistry | None = None) -> None:
        self._registry = registry or PIDRegistry()
        self._singleton = SingletonBindManager(self._registry)

    # ------------------------------------------------------------------
    # API PID Registry
    # ------------------------------------------------------------------

    def register_process(self, pid: int, name: str, repo: str, role: str, port: int, meta: dict | None = None) -> ProcessEntry:
        fingerprint = SingletonBindManager.probe_fingerprint(port) or ""
        entry = ProcessEntry(
            pid=pid,
            name=name,
            repo=repo,
            role=role,
            port=port,
            started_at=datetime.now(timezone.utc).isoformat(),
            last_seen=datetime.now(timezone.utc).isoformat(),
            fingerprint=fingerprint,
            meta=meta or {},
        )
        self._registry.register(entry)
        return entry

    def unregister_process(self, pid: int) -> None:
        self._registry.unregister(pid)

    def list_processes(self) -> list[dict[str, Any]]:
        self._registry.prune_dead()
        return [e.to_dict() for e in self._registry.list_all()]

    def get_process(self, pid: int) -> Optional[dict[str, Any]]:
        entry = self._registry.get(pid)
        return entry.to_dict() if entry else None

    # ------------------------------------------------------------------
    # API Singleton Bind
    # ------------------------------------------------------------------

    def check_singleton(self, port: int, service_name: str, expected_fingerprint: str | None = None) -> dict[str, Any]:
        result = self._singleton.preflight(port, service_name, expected_fingerprint)
        return result.to_dict()

    def probe_fingerprint(self, port: int, health_path: str = "/healthz") -> Optional[str]:
        return SingletonBindManager.probe_fingerprint(port, health_path)

    # ------------------------------------------------------------------
    # API Native Process (Win32)
    # ------------------------------------------------------------------

    @staticmethod
    def is_alive(pid: int) -> bool:
        return _is_process_alive(pid)

    @staticmethod
    def terminate(pid: int, force: bool = True) -> dict[str, Any]:
        """Terminate a process by PID using native Win32 API when available."""
        try:
            if sys.platform == "win32":
                cmd = ["taskkill", "/F" if force else "/PID", str(pid)]
                result = subprocess.run(cmd, capture_output=True, text=True)
                return {
                    "ok": result.returncode == 0,
                    "pid": pid,
                    "stdout": result.stdout.strip(),
                    "stderr": result.stderr.strip(),
                }
            import os as _os
            _os.kill(pid, 9 if force else 15)
            return {"ok": True, "pid": pid}
        except Exception as exc:
            return {"ok": False, "pid": pid, "error": str(exc)}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_process_alive(pid: int) -> bool:
    if sys.platform == "win32":
        cmd = f"Get-Process -Id {pid} -ErrorAction SilentlyContinue"
        return os.system(f"powershell -Command \"{cmd}\"") == 0
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, OSError):
        return False
