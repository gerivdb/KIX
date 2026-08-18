"""Registry générique des runners KIX."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from runners.base import RunnerBase, RunnerSpec
from runners.python_runner import PythonRunner
from runners.zig_runner import ZigBinaryRunner
from runners.gateway_runner import GatewayRunner

RUNNER_CLASSES: dict[str, type[RunnerBase]] = {
    "python": PythonRunner,
    "zig-binary": ZigBinaryRunner,
    "gateway-exe": GatewayRunner,
}


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def load_runners_config(path: Path) -> list[RunnerSpec]:
    """Charge la liste des runners depuis un fichier runners.yaml."""
    data = _load_yaml(path)
    runners: list[RunnerSpec] = []
    for entry in data.get("runners", []):
        if not isinstance(entry, dict):
            continue
        working_dir = Path(entry.get("working_dir", ""))
        log_file = entry.get("log_file")
        runners.append(
            RunnerSpec(
                name=entry["name"],
                runner_type=entry["runner_type"],
                port=int(entry["port"]),
                working_dir=working_dir,
                entrypoint=entry.get("entrypoint"),
                binary=entry.get("binary"),
                command=entry.get("command"),
                env=entry.get("env"),
                health_path=entry.get("health_path", "/healthz"),
                health_timeout=float(entry.get("health_timeout", 5.0)),
                depends_on=entry.get("depends_on"),
                build=entry.get("build"),
                bootstrap=bool(entry.get("bootstrap", False)),
                auto_start=bool(entry.get("auto_start", True)),
                restart_policy=entry.get("restart_policy"),
                log_file=Path(log_file) if log_file else None,
                meta=entry.get("meta"),
            )
        )
    return runners


def get_runner(spec: RunnerSpec) -> RunnerBase:
    """Fabrique un RunnerBase à partir d'un RunnerSpec."""
    cls = RUNNER_CLASSES.get(spec.runner_type)
    if cls is None:
        raise ValueError(f"Unknown runner_type={spec.runner_type!r} for runner={spec.name!r}")
    return cls(spec)
