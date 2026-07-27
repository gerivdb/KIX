"""KIX orchestrator core logic."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

import requests
import yaml
from flask import Flask, jsonify, request

from src.runner_state import RunnerStateStore

app = Flask(__name__)

STORE = RunnerStateStore(os.environ.get("KIX_DB", str(Path(__file__).resolve().parent.parent / "data" / "kix.sqlite")))
KNOWN_REPO_FILE = Path(__file__).resolve().parents[3] / "L0-CANON" / "GOVERNANCE-HUB" / "known_repositories.yaml"


@dataclass
class Runner:
    name: str
    port: int
    status: str = "unknown"
    pid: Optional[int] = None
    started_at: Optional[str] = None
    last_check: Optional[str] = None
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "port": self.port,
            "status": self.status,
            "pid": self.pid,
            "started_at": self.started_at,
            "last_check": self.last_check,
            "meta": self.meta,
        }


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_known_repositories() -> list[Runner]:
    if not KNOWN_REPO_FILE.exists():
        return []
    with open(KNOWN_REPO_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    runners: list[Runner] = []
    for section in data.values():
        if not isinstance(section, list):
            continue
        for entry in section:
            if not isinstance(entry, dict):
                continue
            name = entry.get("name")
            port = entry.get("port")
            if not name or not port:
                continue
            runners.append(
                Runner(
                    name=name,
                    port=int(port),
                    meta={
                        k: v
                        for k, v in entry.items()
                        if k not in {"name", "port"}
                    },
                )
            )
    return runners


def _is_process_alive(pid: int) -> bool:
    if sys.platform == "win32":
        cmd = f"Get-Process -Id {pid} -ErrorAction SilentlyContinue"
        return os.system(f"powershell -Command \"{cmd}\"") == 0
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, OSError):
        return False


def _probe_port(port: int, timeout: float = 1.0) -> bool:
    if sys.platform == "win32":
        cmd = f"Test-NetConnection -ComputerName localhost -Port {port} -WarningAction SilentlyContinue | Select-Object -ExpandProperty TcpTestSucceeded"
        result = os.popen(f"powershell -Command \"{cmd}\"").read().strip()
        return result == "True"
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        try:
            sock.connect(("localhost", port))
            return True
        except (OSError, ValueError):
            return False


def _sync_runners() -> dict[str, Runner]:
    runners = {r.name: r for r in _load_known_repositories()}
    states = STORE.list_all()
    now = _utcnow()
    for name, runner in runners.items():
        state = states.get(name)
        if state:
            runner.pid = state.pid
            runner.status = state.status
            runner.started_at = state.started_at
            runner.last_check = state.updated_at
        if runner.status in {"running", "starting"} and runner.pid:
            alive = _is_process_alive(runner.pid)
            port_open = _probe_port(runner.port)
            if not alive or not port_open:
                runner.status = "stopped"
                runner.last_check = now
                STORE.upsert(
                    name,
                    status="stopped",
                    pid=runner.pid,
                    started_at=runner.started_at,
                    updated_at=now,
                )
    return runners


@app.get("/health")
def health() -> Any:
    return jsonify({"status": "ok", "service": "kix", "port": 8800})


@app.get("/metrics")
def metrics() -> Any:
    states = STORE.list_all()
    return jsonify(
        {
            "service": "kix",
            "port": 8800,
            "runners_total": len(states),
            "runners_running": sum(1 for s in states.values() if s.status == "running"),
            "runners_stopped": sum(1 for s in states.values() if s.status == "stopped"),
            "timestamp": _utcnow(),
        }
    )


@app.get("/vote")
def vote() -> Any:
    states = STORE.list_all()
    by_status: dict[str, int] = {}
    for s in states.values():
        by_status[s.status] = by_status.get(s.status, 0) + 1
    return jsonify({"vote": "functional", "by_status": by_status})


@app.get("/runners")
def list_runners() -> Any:
    runners = _sync_runners()
    return jsonify({"runners": [r.to_dict() for r in runners.values()], "count": len(runners)})


@app.get("/runners/<string:name>/status")
def runner_status(name: str) -> Any:
    runners = _sync_runners()
    runner = runners.get(name)
    if not runner:
        return jsonify({"error": "runner_not_found", "name": name}), 404
    return jsonify(runner.to_dict())


def _launch_runner(runner: Runner) -> tuple[bool, Optional[str]]:
    root = Path(__file__).resolve().parents[1] / runner.name
    if not root.exists():
        return False, f"runner_dir_missing:{root}"
    main_py = root / "src" / "app.py"
    if not main_py.exists():
        main_py = root / "main.py"
    if not main_py.exists():
        return False, "entrypoint_missing"
    cmd = [sys.executable, str(main_py)]
    log_file = Path(__file__).resolve().parent.parent / "data" / f"{runner.name}.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(log_file, "a", encoding="utf-8") as log:
            log.write(f"[KIX] launching {' '.join(cmd)} at {_utcnow()}\n")
        if sys.platform == "win32":
            proc = subprocess.Popen(
                cmd,
                cwd=root,
                creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
            )
        else:
            proc = subprocess.Popen(cmd, cwd=root, start_new_session=True)
        return True, None
    except (OSError, ValueError) as exc:
        return False, str(exc)


@app.post("/runners/<string:name>/start")
def start_runner(name: str) -> Any:
    runners = _sync_runners()
    runner = runners.get(name)
    if not runner:
        return jsonify({"error": "runner_not_found", "name": name}), 404
    if runner.status == "running":
        return jsonify({"status": "running", "name": name, "pid": runner.pid})
    ok, err = _launch_runner(runner)
    if not ok:
        return jsonify({"error": "launch_failed", "detail": err}), 500
    import time
    time.sleep(0.3)
    alive = _is_process_alive(runner.pid or 0) if runner.pid else _probe_port(runner.port)
    status = "running" if alive else "starting"
    now = _utcnow()
    STORE.upsert(name, status=status, pid=runner.pid, started_at=runner.started_at or now, updated_at=now)
    return jsonify({"status": status, "name": name})


@app.post("/runners/<string:name>/stop")
def stop_runner(name: str) -> Any:
    runners = _sync_runners()
    runner = runners.get(name)
    if not runner:
        return jsonify({"error": "runner_not_found", "name": name}), 404
    if runner.status == "stopped":
        return jsonify({"status": "stopped", "name": name})
    if runner.pid:
        try:
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/F", "/PID", str(runner.pid)], check=False)
            else:
                os.kill(runner.pid, 9)
        except OSError:
            pass
    STORE.upsert(name, status="stopped", pid=None, updated_at=_utcnow())
    return jsonify({"status": "stopped", "name": name})


def _probe_runner_health(runner: Runner) -> dict[str, Any]:
    url = f"http://localhost:{runner.port}/health"
    started = datetime.now(timezone.utc)
    try:
        resp = requests.get(url, timeout=2)
        latency = (datetime.now(timezone.utc) - started).total_seconds()
        payload = {}
        try:
            payload = resp.json() or {}
        except ValueError:
            payload = {}
        if resp.status_code == 200:
            return {
                "name": runner.name,
                "port": runner.port,
                "status": "ok",
                "http_status": resp.status_code,
                "latency_ms": round(latency * 1000, 2),
                "service": payload.get("service"),
            }
        return {
            "name": runner.name,
            "port": runner.port,
            "status": "unhealthy",
            "http_status": resp.status_code,
            "latency_ms": round(latency * 1000, 2),
            "detail": "non_200",
        }
    except requests.RequestException as exc:
        latency = (datetime.now(timezone.utc) - started).total_seconds()
        return {
            "name": runner.name,
            "port": runner.port,
            "status": "unreachable",
            "latency_ms": round(latency * 1000, 2),
            "detail": str(exc),
        }


@app.get("/audit")
def audit() -> Any:
    runners = _sync_runners()
    results: list[dict[str, Any]] = []
    healthy = 0
    workers = min(8, len(runners) or 1)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        future_map = {pool.submit(_probe_runner_health, runner): runner for runner in runners.values()}
        for future in as_completed(future_map):
            data = future.result()
            results.append(data)
            if data.get("status") == "ok":
                healthy += 1
    return jsonify(
        {
            "service": "kix",
            "port": 8800,
            "timestamp": _utcnow(),
            "total": len(results),
            "healthy": healthy,
            "unhealthy": sum(1 for r in results if r.get("status") != "ok"),
            "results": sorted(results, key=lambda x: x.get("name", "")),
        }
    )
