"""KIX L2RunnerOrchestrator — Adapter for base_orchestrator adoption.

Architecture:
- L2RunnerOrchestrator extends BaseOrchestrator
- KIXProcessManagerAdapter implements ProcessManagerInterface
- KIXRegistryAdapter implements RegistryInterface
- KIXHealthAdapter implements HealthCheckerInterface
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from base_orchestrator import (
    BaseOrchestrator,
    RegistryInterface,
    ProcessManagerInterface,
    HealthCheckerInterface,
    DeployerInterface,
    HTTPServerInterface,
    ActorSpec,
    ProcessEntry,
)
try:
    from process_manager import ProcessManager, ProcessEntry as KIXProcessEntry
except ImportError:
    from src.process_manager import ProcessManager, ProcessEntry as KIXProcessEntry
from kix.runner_base import BaseRunner


class KIXProcessManagerAdapter(ProcessManagerInterface):
    """Adapter from KIX ProcessManager to ProcessManagerInterface."""

    def __init__(self, process_manager: ProcessManager) -> None:
        self._process_manager = process_manager

    def register(self, entry: ProcessEntry) -> None:
        kix_entry = KIXProcessEntry(
            pid=entry.pid,
            name=entry.actor_id,
            repo="kix",
            role=entry.role,
            port=0,
            started_at=entry.started_at.isoformat() if hasattr(entry.started_at, 'isoformat') else str(entry.started_at),
            last_seen=entry.last_seen.isoformat() if hasattr(entry.last_seen, 'isoformat') else str(entry.last_seen),
            fingerprint="",
        )
        self._process_manager.register_process(
            pid=kix_entry.pid,
            name=kix_entry.name,
            repo=kix_entry.repo,
            role=kix_entry.role,
            port=kix_entry.port,
            meta={"fingerprint": ""},
        )

    def unregister(self, pid: int) -> None:
        self._process_manager.unregister_process(pid)

    def get(self, pid: int) -> ProcessEntry | None:
        data = self._process_manager.get_process(pid)
        if data is None:
            return None
        return ProcessEntry(
            pid=data["pid"],
            actor_id=data.get("name", ""),
            role=data.get("role", "actor"),
            started_at=data.get("started_at", ""),
            last_seen=data.get("last_seen", ""),
        )

    def prune_dead(self) -> list[int]:
        return self._process_manager.list_processes()


class KIXRegistryAdapter(RegistryInterface):
    """Adapter from KIX runner registry to RegistryInterface."""

    def __init__(self, runner_registry: dict[str, BaseRunner]) -> None:
        self._runner_registry = runner_registry

    def load(self) -> None:
        pass

    def get_actor(self, actor_id: str) -> ActorSpec | None:
        runner = self._runner_registry.get(actor_id)
        if runner is None:
            return None
        spec = runner.spec
        return ActorSpec(
            id=spec.name,
            command=spec.entrypoint or "",
            working_dir=str(spec.working_dir),
            auto_restart=spec.auto_start,
            restart_delay=10,
            deployment=spec.meta or {},
        )

    def list_actors(self) -> list[str]:
        return list(self._runner_registry.keys())


class KIXHealthAdapter(HealthCheckerInterface):
    """Adapter from KIX health to HealthCheckerInterface."""

    def __init__(self, health_checker: Any) -> None:
        self._health_checker = health_checker

    def check_all(self) -> dict[str, Any]:
        if hasattr(self._health_checker, "check_all"):
            return self._health_checker.check_all()
        return {}

    def check_actor(self, actor_id: str) -> dict[str, Any]:
        if hasattr(self._health_checker, "check_runner"):
            return self._health_checker.check_runner(actor_id)
        return {}


class L2RunnerOrchestrator(BaseOrchestrator):
    """KIX L2 orchestrator for runners.

    Adopts base_orchestrator primitive for L2-PLATFORM.
    """

    def __init__(
        self,
        runner_registry: dict[str, BaseRunner],
        process_manager: ProcessManager,
        health_checker: Any | None = None,
    ) -> None:
        registry_adapter = KIXRegistryAdapter(runner_registry)
        pid_adapter = KIXProcessManagerAdapter(process_manager)
        health_adapter = KIXHealthAdapter(health_checker) if health_checker else None

        super().__init__(
            registry=registry_adapter,
            process_manager=pid_adapter,
            health_checker=health_adapter,
            deployer=None,
            http_server=None,
        )
