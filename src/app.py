"""KIX orchestrator core logic."""

from __future__ import annotations

import json
import os
import sqlite3
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
from src.notification_store import NotificationStore
from src.notification_metrics import NotificationMetricsStore
from src.auth import login_required, create_token, _load_users
from src.audit_log import AuditLogStore
from src.zombie_monitor import zombie_bp
from runners.registry import load_runners_config, get_runner
from runners.base import RunnerBase, RunnerSpec

app = Flask(__name__)
app.register_blueprint(zombie_bp)

STORE = RunnerStateStore(os.environ.get("KIX_DB", str(Path(__file__).resolve().parent.parent / "data" / "kix.sqlite")))
NOTIFICATIONS = NotificationStore(os.environ.get("KIX_NOTIFICATIONS_DB", str(Path(__file__).resolve().parent.parent / "data" / "notifications.db")))
METRICS = NotificationMetricsStore(os.environ.get("KIX_METRICS_DB", str(Path(__file__).resolve().parent.parent / "data" / "metrics.db")))
AUDIT_LOG = AuditLogStore(os.environ.get("KIX_AUDIT_DB", str(Path(__file__).resolve().parent.parent / "data" / "audit.db")))
KNOWN_REPO_FILE = Path(os.environ.get("KIX_KNOWN_REPOS_FILE", str(Path(__file__).resolve().parents[3] / "L0-CANON" / "GOVERNANCE-HUB" / "known_repositories.yaml")))


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
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        try:
            sock.connect(("localhost", port))
            return True
        except (OSError, ValueError):
            return False


def _probe_http(port: int, path: str, timeout: float = 1.0, headers: dict | None = None) -> dict:
    import requests

    url = f"http://localhost:{port}{path}"
    try:
        resp = requests.get(url, timeout=timeout, headers=headers or {})
        if resp.status_code == 200:
            return {"status": "ok", "http_status": resp.status_code}
        return {"status": "unhealthy", "http_status": resp.status_code}
    except Exception as exc:
        return {"status": "unreachable", "detail": str(exc)}


def _sync_runners() -> dict[str, Runner]:
    runners = {r.name: r for r in _load_known_repositories()}

    # Merge Generic Runner Wrapper config (config/runners.yaml)
    for spec in _load_runners_config():
        runners[spec.name] = Runner(
            name=spec.name,
            port=spec.port,
            meta={
                "runner_type": spec.runner_type,
                "working_dir": str(spec.working_dir),
                "entrypoint": spec.entrypoint,
                "binary": spec.binary,
                "health_path": spec.health_path,
                "restart_policy": spec.restart_policy,
                "bootstrap": spec.bootstrap,
                "auto_start": spec.auto_start,
                "log_file": str(spec.log_file) if spec.log_file else None,
                "repo": (spec.meta or {}).get("repo", ""),
                "role": (spec.meta or {}).get("role", ""),
                "headers": spec.headers,
            },
        )

    if "MEM-CORE" not in runners:
        runners["MEM-CORE"] = Runner(name="MEM-CORE", port=8907)
    states = STORE.list_all()
    now = _utcnow()

    # Fusionner l'état STORE (pid/status) puis probe actif sur tous les ports
    # pour refléter la réalité (running/stopped) au lieu de "unknown".
    for name, runner in runners.items():
        state = states.get(name)
        if state:
            runner.pid = state.pid
            runner.started_at = state.started_at
            runner.last_check = state.updated_at

    def _check(runner: Runner) -> None:
        headers = (runner.meta or {}).get("headers") or {}
        health_path = (runner.meta or {}).get("health_path") or "/health"
        health = _probe_http(runner.port, health_path, timeout=0.5, headers=headers)
        if health.get("status") == "ok":
            runner.status = "running"
            runner.last_check = now
        else:
            runner.status = "stopped"
            runner.last_check = now
            if runner.pid:
                STORE.upsert(
                    runner.name,
                    status="stopped",
                    pid=runner.pid,
                    started_at=runner.started_at,
                    updated_at=now,
                )

    with ThreadPoolExecutor(max_workers=min(8, len(runners) or 1)) as pool:
        list(pool.map(_check, list(runners.values())))

    return runners


_RUNNERS_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "runners.yaml"
_RUNNER_INSTANCES: dict[str, RunnerBase] = {}


def _load_runners_config() -> list[RunnerSpec]:
    """Charge la configuration déclarative des runners depuis runners.yaml."""
    return load_runners_config(_RUNNERS_CONFIG_PATH)


def _get_runner_instance(name: str) -> RunnerBase | None:
    """Retourne une instance RunnerBase pour le runner nommé, ou None."""
    if name not in _RUNNER_INSTANCES:
        for spec in _load_runners_config():
            if spec.name == name:
                _RUNNER_INSTANCES[name] = get_runner(spec)
                break
    return _RUNNER_INSTANCES.get(name)


def _load_phi_cps_history(limit: int = 20) -> list[dict[str, Any]]:
    default_db = Path(__file__).resolve().parent.parent / "data" / "kix.sqlite"
    bridge_db = Path(os.environ.get("KIX_MIMIR_METRICS_DB", str(Path(__file__).resolve().parent.parent / "scripts" / ".." / "L3-CITIZENS" / "MIMIR" / "data" / "metrics.db")))
    bridge_db = bridge_db.resolve()
    db_path = bridge_db if bridge_db.exists() else default_db
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT ts, value FROM phi_cps ORDER BY ts DESC LIMIT ?", (limit,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def _load_recent_alerts(limit: int = 10) -> list[dict[str, Any]]:
    bridge_db = Path(os.environ.get("KIX_MIMIR_METRICS_DB", str(Path(__file__).resolve().parent.parent / "scripts" / ".." / "L3-CITIZENS" / "MIMIR" / "data" / "metrics.db")))
    bridge_db = bridge_db.resolve()
    if not bridge_db.exists():
        return []
    try:
        conn = sqlite3.connect(bridge_db)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT ts, triggered, phi_cps, threshold, payload FROM alerts ORDER BY ts DESC LIMIT ?",
            (limit,),
        ).fetchall()
        conn.close()
        results = []
        for r in rows:
            item = dict(r)
            try:
                payload = json.loads(item["payload"] or "{}")
                item["items"] = payload.get("items", [])
            except Exception:
                item["items"] = []
            results.append(item)
        return results
    except Exception:
        return []


@app.get("/health")
def health() -> Any:
    return jsonify({"status": "ok", "service": "kix", "port": 8800})


@app.get("/healthz")
def healthz() -> Any:
    return jsonify({"status": "ok"})


@app.get("/readyz")
def readyz() -> Any:
    checks: dict[str, Any] = {"kix": "ok"}
    try:
        db_path = os.environ.get("KIX_DB", str(Path(__file__).resolve().parent.parent / "data" / "kix.sqlite"))
        conn = sqlite3.connect(db_path)
        conn.execute("SELECT 1")
        conn.close()
        checks["runner_store"] = "ok"
    except Exception:
        checks["runner_store"] = "error"
        return jsonify({"status": "degraded", "checks": checks}), 503
    try:
        notifications_db = os.environ.get("KIX_NOTIFICATIONS_DB", str(Path(__file__).resolve().parent.parent / "data" / "notifications.db"))
        conn = sqlite3.connect(notifications_db)
        conn.execute("SELECT 1")
        conn.close()
        checks["notifications"] = "ok"
    except Exception:
        checks["notifications"] = "error"
    try:
        audit_db = os.environ.get("KIX_AUDIT_DB", str(Path(__file__).resolve().parent.parent / "data" / "audit.db"))
        conn = sqlite3.connect(audit_db)
        conn.execute("SELECT 1")
        conn.close()
        checks["audit"] = "ok"
    except Exception:
        checks["audit"] = "error"
    status = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    code = 200 if status == "ok" else 503
    return jsonify({"status": status, "checks": checks}), code


@app.post("/login")
def login() -> Any:
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"error": "missing_credentials"}), 400
    users = _load_users()
    user = users.get(username)
    if not user or user["password"] != password:
        return jsonify({"error": "invalid_credentials"}), 401
    token = create_token(username, user["role"])
    return jsonify({"access_token": token, "role": user["role"], "username": username})


@app.get("/metrics")
def metrics() -> Any:
    states = STORE.list_all()
    notif_metrics = METRICS.list_all()
    notif_channels = {
        channel: {
            "total_sent": m.total_sent,
            "total_success": m.total_success,
            "total_failed": m.total_failed,
            "success_rate": round(m.total_success / m.total_sent, 3) if m.total_sent else 0.0,
            "avg_latency_ms": round(m.avg_latency_ms, 2),
            "last_sent_at": m.last_sent_at,
        }
        for channel, m in notif_metrics.items()
    }
    return jsonify(
        {
            "service": "kix",
            "port": 8800,
            "runners_total": len(states),
            "runners_running": sum(1 for s in states.values() if s.status == "running"),
            "runners_stopped": sum(1 for s in states.values() if s.status == "stopped"),
            "notifications": notif_channels,
            "timestamp": _utcnow(),
        }
    )


@app.get("/metrics/prometheus")
def metrics_prometheus() -> Any:
    notif_metrics = METRICS.list_all()
    lines = [
        "# HELP kix_notification_total_total Total notifications sent per channel",
        "# TYPE kix_notification_total_total counter",
    ]
    for channel, m in notif_metrics.items():
        lines.append(f'kix_notification_total_total{{channel="{channel}"}} {m.total_sent}')
    lines.append("# HELP kix_notification_success_total Total successful notifications per channel")
    lines.append("# TYPE kix_notification_success_total counter")
    for channel, m in notif_metrics.items():
        lines.append(f'kix_notification_success_total{{channel="{channel}"}} {m.total_success}')
    lines.append("# HELP kix_notification_failed_total Total failed notifications per channel")
    lines.append("# TYPE kix_notification_failed_total counter")
    for channel, m in notif_metrics.items():
        lines.append(f'kix_notification_failed_total{{channel="{channel}"}} {m.total_failed}')
    lines.append("# HELP kix_notification_latency_seconds Average notification latency per channel")
    lines.append("# TYPE kix_notification_latency_seconds gauge")
    for channel, m in notif_metrics.items():
        lines.append(f'kix_notification_latency_seconds{{channel="{channel}"}} {round(m.avg_latency_ms / 1000, 4)}')
    return app.response_class(
        "\n".join(lines) + "\n",
        mimetype="text/plain; version=0.0.4",
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
    if runner.name == "MEM-CORE":
        try:
            resp = requests.get(f"http://localhost:{runner.port}/healthz", timeout=2)
            runner.status = "running" if resp.status_code == 200 else "stopped"
            runner.meta["api_status"] = resp.status_code
        except requests.RequestException:
            runner.status = "stopped"
            runner.meta["api_status"] = None
    return jsonify(runner.to_dict())


@app.get("/status/cross-service")
def cross_service_status() -> Any:
    try:
        from src.auto_remediation import AutoRemediationEngine
        engine = AutoRemediationEngine(os.environ.get("KIX_REMEDIATION_DB", str(Path(__file__).resolve().parent.parent / "data" / "remediation.db")))
        policies = engine.list_policies()
    except Exception:
        policies = []
    runners = _sync_runners()
    snapshot = {
        "timestamp": _utcnow(),
        "service": "kix",
        "runners": {name: runner.to_dict() for name, runner in runners.items()},
        "remediation_policies": [p.to_dict() if hasattr(p, "to_dict") else dict(p) for p in policies],
        "notification_metrics": METRICS.list_all(),
    }
    return jsonify(snapshot)



@app.post("/runners/<string:name>/start")
@login_required(roles=["admin", "operator"])
def start_runner(name: str) -> Any:
    runners = _sync_runners()
    runner = runners.get(name)
    if not runner:
        return jsonify({"error": "runner_not_found", "name": name}), 404
    if runner.status == "running":
        return jsonify({"status": "running", "name": name, "pid": runner.pid})

    # Phase 1 — préférer le nouveau système runners.yaml
    instance = _get_runner_instance(name)
    if instance is not None:
        result = instance.start()
        pid = result.get("pid")
        status = result.get("status", "starting")
        now = _utcnow()
        STORE.upsert(name, status=status, pid=pid, started_at=now, updated_at=now)
        AUDIT_LOG.record(
            "runner_start",
            f"/runners/{name}/start",
            "POST",
            getattr(request, "user", {}).get("sub"),
            details=f"started {name} via runner wrapper",
            ip_address=request.remote_addr,
        )
        return jsonify({"status": status, "name": name, "pid": pid})


@app.post("/runners/register")
def register_runner() -> Any:
    """Enregistre un runner dans KIX sans authentification (interne bootstrap)."""
    if not request.is_json:
        return jsonify({"error": "body_must_be_json"}), 400
    data = request.get_json() or {}
    name = data.get("name")
    port = data.get("port")
    status = data.get("status", "running")
    if not name or port is None:
        return jsonify({"error": "missing_fields", "details": "name and port are required"}), 400
    now = _utcnow()
    STORE.upsert(name, status=status, pid=None, started_at=now, updated_at=now)
    return jsonify({"status": "registered", "name": name, "port": port, "runner_status": status}), 200


# ==================== NEW ENDPOINTS FOR P2 ====================
@app.post("/schedule/cycle")
@login_required(roles=["admin", "operator"])
def schedule_cycle() -> Any:
    """
    Schedule a new operational cycle for a service.
    Body format:
    {
        "service": "PLIX",
        "cron": "0 0 * * *",  # cron expression
        "action": "backup"   # action to execute on schedule
    }
    """
    if not request.is_json:
        return jsonify({"error": "body_must_be_json"}), 400
    
    data = request.get_json()
    service = data.get("service")
    cron = data.get("cron")
    action = data.get("action")
    
    if not service or not cron or not action:
        return jsonify({"error": "missing_fields", "details": "service, cron, and action are required"}), 400
    
    # Store the schedule in the database (simplified approach)
    schedule = {
        "service": service,
        "cron": cron,
        "action": action,
        "created_at": _utcnow(),
        "created_by": getattr(request, "user", {}).get("sub", "anonymous")
    }
    
    # Save schedule to persistent storage
    schedules = load_schedules()
    schedules.append(schedule)
    save_schedules(schedules)
    
    return jsonify({
        "status": "scheduled",
        "service": service,
        "cron": cron,
        "action": action,
        "schedule_id": len(schedules) - 1
    })


def load_schedules() -> list[dict[str, Any]]:
    """Load schedules from persistent storage."""
    schedule_file = Path(__file__).resolve().parents[1] / "data" / "schedules.json"
    if schedule_file.exists():
        try:
            with open(schedule_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_schedules(schedules: list[dict[str, Any]]) -> None:
    """Save schedules to persistent storage."""
    schedule_file = Path(__file__).resolve().parents[1] / "data" / "schedules.json"
    # Ensure parent directory exists
    schedule_file.parent.mkdir(parents=True, exist_ok=True)
    with open(schedule_file, "w", encoding="utf-8") as f:
        json.dump(schedules, f, indent=2)


@app.delete("/schedule/cycle/<int:schedule_id>")
@login_required(roles=["admin", "operator"])
def delete_schedule(schedule_id: int) -> Any:
    """Delete a schedule by ID."""
    schedules = load_schedules()
    if schedule_id < 0 or schedule_id >= len(schedules):
        return jsonify({"error": "schedule_not_found"}), 404
    
    deleted = schedules.pop(schedule_id)
    save_schedules(schedules)
    
    return jsonify({
        "status": "deleted",
        "service": deleted["service"],
        "schedule_id": schedule_id
    })


@app.get("/schedules")
@login_required(roles=["admin", "operator"])
def list_schedules() -> Any:
    """List all scheduled cycles."""
    schedules = load_schedules()
    return jsonify({"total": len(schedules), "schedules": schedules})


@app.post("/runners/<string:name>/stop")
@login_required(roles=["admin", "operator"])
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
    AUDIT_LOG.record(
        "runner_stop",
        f"/runners/{name}/stop",
        "POST",
        getattr(request, "user", {}).get("sub"),
        details=f"stopped {name}",
        ip_address=request.remote_addr,
    )
    return jsonify({"status": "stopped", "name": name})


@app.get("/runners/<string:name>/health")
def runner_health(name: str) -> Any:
    runner = _get_runner_instance(name)
    if runner is None:
        return jsonify({"error": "runner_not_found", "name": name}), 404
    result = runner.health()
    code = 200 if result.get("status") == "ok" else 503
    return jsonify(result), code


@app.get("/runners/<string:name>/logs")
def runner_logs(name: str) -> Any:
    runner = _get_runner_instance(name)
    if runner is None:
        return jsonify({"error": "runner_not_found", "name": name}), 404
    lines = int(request.args.get("lines", "100"))
    content = runner.logs(lines=lines)
    return app.response_class(content, mimetype="text/plain; charset=utf-8")


@app.post("/runners/<string:name>/restart")
@login_required(roles=["admin", "operator"])
def restart_runner(name: str) -> Any:
    runners = _sync_runners()
    runner = runners.get(name)
    if not runner:
        return jsonify({"error": "runner_not_found", "name": name}), 404
    instance = _get_runner_instance(name)
    if instance is None:
        return jsonify({"error": "runner_not_configured", "name": name}), 404
    pid = runner.pid
    if pid:
        result = instance.restart(pid)
    else:
        result = instance.start()
    now = _utcnow()
    status = result.get("status", "starting")
    STORE.upsert(name, status=status, pid=result.get("pid"), started_at=now, updated_at=now)
    AUDIT_LOG.record(
        "runner_restart",
        f"/runners/{name}/restart",
        "POST",
        getattr(request, "user", {}).get("sub"),
        details=f"restarted {name}",
        ip_address=request.remote_addr,
    )
    return jsonify({"status": status, "name": name, "pid": result.get("pid")})


@app.get("/doctor")
def doctor() -> Any:
    runners = _load_runners_config()
    results: list[dict[str, Any]] = []
    for spec in runners:
        instance = get_runner(spec)
        health = instance.health()
        results.append(
            {
                "name": spec.name,
                "runner_type": spec.runner_type,
                "port": spec.port,
                "health": health,
                "restart_policy": spec.restart_policy,
                "bootstrap": spec.bootstrap,
            }
        )
    unhealthy = [r for r in results if r["health"].get("status") != "ok"]
    return jsonify(
        {
            "service": "kix",
            "timestamp": _utcnow(),
            "total": len(results),
            "healthy": len(results) - len(unhealthy),
            "unhealthy": len(unhealthy),
            "runners": results,
            "unhealthy_runners": unhealthy,
        }
    )


@app.post("/doctor/run")
@login_required(roles=["admin", "operator"])
def doctor_run() -> Any:
    runners = _load_runners_config()
    restarted: list[dict[str, Any]] = []
    for spec in runners:
        if spec.restart_policy is None:
            continue
        instance = get_runner(spec)
        health = instance.health()
        if health.get("status") != "ok":
            stored = STORE.list_all().get(spec.name)
            pid = stored.pid if stored else None
            if pid:
                result = instance.restart(pid)
                restarted.append(
                    {
                        "name": spec.name,
                        "action": "restarted",
                        "result": result,
                    }
                )
            else:
                result = instance.start()
                restarted.append(
                    {
                        "name": spec.name,
                        "action": "started",
                        "result": result,
                    }
                )
    return jsonify({"restarted": restarted, "count": len(restarted)})


@app.get("/swarm/status")
def swarm_status() -> Any:
    runners = _load_runners_config()
    swarm: dict[str, Any] = {
        "service": "kix",
        "timestamp": _utcnow(),
        "runners": {},
    }
    for spec in runners:
        instance = get_runner(spec)
        health = instance.health()
        stored = STORE.list_all().get(spec.name)
        swarm["runners"][spec.name] = {
            "runner_type": spec.runner_type,
            "port": spec.port,
            "status": health.get("status"),
            "restart_policy": spec.restart_policy,
            "bootstrap": spec.bootstrap,
            "pid": stored.pid if stored else None,
            "health": health,
        }
    return jsonify(swarm)


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


@app.get("/probe/audit")
def probe_audit() -> Any:
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
    total = len(results)
    healthy_count = healthy
    phi_cps = round((healthy_count / total), 3) if total else 0.0
    return jsonify(
        {
            "service": "kix",
            "port": 8800,
            "timestamp": _utcnow(),
            "total": total,
            "healthy": healthy_count,
            "unhealthy": sum(1 for r in results if r.get("status") != "ok"),
            "phi_cps": phi_cps,
            "results": sorted(results, key=lambda x: x.get("name", "")),
        }
    )


@app.get("/audit")
@login_required(roles=["admin"])
def action_audit() -> Any:
    limit = int(request.args.get("limit", "100"))
    items = AUDIT_LOG.list_recent(limit=limit)
    return jsonify(
        {
            "service": "kix",
            "port": 8800,
            "count": len(items),
            "audit": items,
        }
    )


@app.get("/alerts")
def alerts() -> Any:
    threshold = 0.9
    try:
        env_threshold = os.environ.get("KIX_ALERT_THRESHOLD")
        if env_threshold is not None:
            threshold = float(env_threshold)
    except (TypeError, ValueError):
        pass
    service_filter = request.args.get("service")
    runners = _sync_runners()
    results: list[dict[str, Any]] = []
    workers = min(8, len(runners) or 1)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        future_map = {pool.submit(_probe_runner_health, runner): runner for runner in runners.values()}
        for future in as_completed(future_map):
            results.append(future.result())
    total = len(results)
    healthy = sum(1 for r in results if r.get("status") == "ok")
    phi_cps = round((healthy / total), 3) if total else 0.0
    items: list[dict[str, Any]] = []
    for item in results:
        if item.get("status") != "ok":
            if service_filter and item.get("name") != service_filter:
                continue
            items.append(
                {
                    "name": item.get("name"),
                    "port": item.get("port"),
                    "status": item.get("status"),
                    "latency_ms": item.get("latency_ms"),
                    "detail": item.get("detail"),
                }
            )
    triggered = phi_cps < threshold
    return jsonify(
        {
            "service": "kix",
            "port": 8800,
            "timestamp": _utcnow(),
            "triggered": triggered,
            "phi_cps": phi_cps,
            "threshold": threshold,
            "unhealthy": len(items),
            "items": items,
        }
    )


@app.get("/events")
def events() -> Any:
    threshold = 0.9
    try:
        env_threshold = os.environ.get("KIX_ALERT_THRESHOLD")
        if env_threshold is not None:
            threshold = float(env_threshold)
    except (TypeError, ValueError):
        pass
    runners = _sync_runners()
    results: list[dict[str, Any]] = []
    workers = min(8, len(runners) or 1)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        future_map = {pool.submit(_probe_runner_health, runner): runner for runner in runners.values()}
        for future in as_completed(future_map):
            results.append(future.result())
    total = len(results)
    healthy = sum(1 for r in results if r.get("status") == "ok")
    phi_cps = round((healthy / total), 3) if total else 0.0
    payload = json.dumps(
        {
            "service": "kix",
            "port": 8800,
            "timestamp": _utcnow(),
            "triggered": phi_cps < threshold,
            "phi_cps": phi_cps,
            "threshold": threshold,
            "total": total,
            "healthy": healthy,
            "unhealthy": total - healthy,
            "results": sorted(results, key=lambda x: x.get("name", "")),
        }
    )
    return app.response_class(
        f"event: message\ndata: {payload}\n\n",
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@app.get("/notifications/history")
def notifications_history() -> Any:
    limit = int(request.args.get("limit", "100"))
    service = request.args.get("service")
    records = NOTIFICATIONS.list_recent(limit=limit, service=service)
    return jsonify(
        {
            "service": "kix",
            "port": 8800,
            "count": len(records),
            "notifications": [
                {
                    "id": r.id,
                    "event": r.event,
                    "timestamp": r.timestamp,
                    "phi_cps": r.phi_cps,
                    "threshold": r.threshold,
                    "consecutive_cycles": r.consecutive_cycles,
                    "service": r.service,
                    "channel": r.channel,
                    "payload": r.payload,
                }
                for r in records
            ],
        }
    )


@app.get("/remediation/status")
@login_required(roles=["admin"])
def remediation_status() -> Any:
    remediation_db = os.environ.get("KIX_REMEDIATION_DB", str(Path(__file__).resolve().parent.parent / "data" / "remediation.db"))
    try:
        from src.auto_remediation import RemediationStore

        store = RemediationStore(remediation_db)
        items = store.list_recent(limit=100)
        AUDIT_LOG.record(
            "remediation_status_view",
            "/remediation/status",
            "GET",
            getattr(request, "user", {}).get("sub"),
            ip_address=request.remote_addr,
        )
        return jsonify(
            {
                "service": "kix",
                "port": 8800,
                "count": len(items),
                "remediations": items,
            }
        )
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.get("/dashboard")
def dashboard() -> Any:
    runners = _sync_runners()
    rows: list[str] = []
    for runner in runners.values():
        if runner.status == "running":
            badge = '<span class="badge ok">running</span>'
        elif runner.status == "stopped":
            badge = '<span class="badge stopped">stopped</span>'
        elif runner.status == "starting":
            badge = '<span class="badge starting">starting</span>'
        else:
            badge = f'<span class="badge unknown">{runner.status}</span>'
        rows.append(
            "<tr>"
            f"<td>{runner.name}</td>"
            f"<td>{runner.port}</td>"
            f"<td>{badge}</td>"
            f"<td>{runner.pid or ''}</td>"
            f"<td>{runner.last_check or ''}</td>"
            "</tr>"
        )
    body = "\n".join(rows)
    history = _load_phi_cps_history(limit=100)
    latest_phi = history[0]["value"] if history else None
    chart_data = json.dumps([{"ts": h["ts"], "value": h["value"]} for h in reversed(history)])
    history_rows = []
    for item in history[:20]:
        ts = item.get("ts")
        value = item.get("value")
        dt = datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat() if ts else ""
        history_rows.append(f"<tr><td>{dt}</td><td>{value}</td></tr>")
    history_body = "\n".join(reversed(history_rows))
    alerts = _load_recent_alerts(limit=10)
    alert_rows = []
    for item in alerts:
        ts = item.get("ts")
        dt = datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat() if ts else ""
        phi_cps = item.get("phi_cps")
        threshold = item.get("threshold")
        alert_items = item.get("items") or []
        service_names = ", ".join(x.get("name", "?") for x in alert_items[:5])
        if len(alert_items) > 5:
            service_names += f" (+{len(alert_items) - 5})"
        triggered_badge = '<span class="badge alert-triggered">YES</span>' if item.get("triggered") else '<span class="badge alert-skipped">NO</span>'
        alert_rows.append(
            "<tr>"
            f"<td>{dt}</td>"
            f"<td>{triggered_badge}</td>"
            f"<td>{phi_cps}</td>"
            f"<td>{threshold}</td>"
            f"<td>{service_names}</td>"
            "</tr>"
        )
    alert_body = "\n".join(reversed(alert_rows))
    notif_metrics = METRICS.list_all()
    metrics_rows = []
    for channel, m in notif_metrics.items():
        success_rate = round(m.total_success / m.total_sent, 3) if m.total_sent else 0.0
        metrics_rows.append(
            "<tr>"
            f"<td>{channel}</td>"
            f"<td>{m.total_sent}</td>"
            f"<td>{m.total_success}</td>"
            f"<td>{m.total_failed}</td>"
            f"<td>{success_rate}</td>"
            f"<td>{round(m.avg_latency_ms, 2)}</td>"
            f"<td>{m.last_sent_at or ''}</td>"
            "</tr>"
        )
    metrics_body = "\n".join(metrics_rows)
    total = len(runners)
    healthy = sum(1 for r in runners.values() if r.status == "running")
    unhealthy = total - healthy
    phi_display = f"{latest_phi:.3f}" if latest_phi is not None else "--"
    html = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<title>KIX Dashboard</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 2rem; background: #f6f8fa; color: #1f2937; }}
.cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 1rem; margin-bottom: 1.5rem; }}
.card {{ background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 1rem; box-shadow: 0 1px 2px rgba(0,0,0,0.04); }}
.card h3 {{ margin: 0 0 0.5rem; font-size: 0.85rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.05em; }}
.card .value {{ font-size: 1.6rem; font-weight: 700; }}
.card .ok {{ color: #2a9d8f; }}
.card .danger {{ color: #d62828; }}
.card .muted {{ color: #6c757d; }}
a {{ color: #2563eb; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
.section {{ background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 1rem; margin-bottom: 1.25rem; }}
.section h2 {{ margin: 0 0 0.75rem; font-size: 1.1rem; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #e5e7eb; padding: 0.5rem; text-align: left; }}
.badge.ok {{ color: #fff; background: #2a9d8f; padding: 0.2rem 0.5rem; border-radius: 4px; }}
.badge.stopped {{ color: #fff; background: #e76f51; padding: 0.2rem 0.5rem; border-radius: 4px; }}
.badge.starting {{ color: #fff; background: #e9c46a; padding: 0.2rem 0.5rem; border-radius: 4px; }}
.badge.unknown {{ color: #fff; background: #9ca3af; padding: 0.2rem 0.5rem; border-radius: 4px; }}
.badge.alert-triggered {{ color: #fff; background: #d62828; padding: 0.2rem 0.5rem; border-radius: 4px; }}
.badge.alert-skipped {{ color: #fff; background: #6c757d; padding: 0.2rem 0.5rem; border-radius: 4px; }}
#phi {{ font-size: 1.1rem; margin-bottom: 1rem; color: #374151; }}
.controls {{ display: inline-flex; gap: 0.5rem; margin-bottom: 0.5rem; }}
.controls button {{ background: #fff; border: 1px solid #d1d5db; padding: 0.35rem 0.7rem; border-radius: 6px; cursor: pointer; }}
.controls button.active {{ background: #2563eb; color: #fff; border-color: #2563eb; }}
canvas {{ max-width: 100%; height: 240px; }}
#alertPoll {{ margin-left: 0.5rem; font-size: 0.85rem; color: #6b7280; }}
</style>
</head>
<body>
<h1>KIX Dashboard</h1>
<div class="cards">
  <div class="card"><h3>Runners</h3><div class="value">{total}</div></div>
  <div class="card"><h3>Healthy</h3><div class="value ok">{healthy}</div></div>
  <div class="card"><h3>Unhealthy</h3><div class="value danger">{unhealthy}</div></div>
  <div class="card"><h3>φ-CPS</h3><div class="value muted">{phi_display}</div></div>
</div>
<div class="section">
  <h2>φ-CPS History</h2>
  <div class="controls">
    <button onclick="setLimit(20)" id="btn-20">20</button>
    <button onclick="setLimit(50)" id="btn-50">50</button>
    <button onclick="setLimit(100)" id="btn-100">100</button>
  </div>
  <canvas id="phiChart"></canvas>
  <p id="phi">φ-CPS: {phi_display} | Updated: {_utcnow()}</p>
</div>
<div class="section">
  <h2>Runners <a href="/runners">/runners</a> <span id="alertPoll">Alerts: live</span></h2>
  <table>
  <thead>
  <tr><th>Name</th><th>Port</th><th>Status</th><th>Pid</th><th>Last check</th></tr>
  </thead>
  <tbody>
  {body}
  </tbody>
  </table>
</div>
<div class="section">
  <h2>Recent Alerts</h2>
  <table>
  <thead>
  <tr><th>Timestamp</th><th>Triggered</th><th>φ-CPS</th><th>Threshold</th><th>Services</th></tr>
  </thead>
  <tbody>
  {alert_body}
  </tbody>
  </table>
</div>
<div class="section">
  <h2>Notification Metrics</h2>
  <table>
  <thead>
  <tr><th>Channel</th><th>Total Sent</th><th>Success</th><th>Failed</th><th>Success Rate</th><th>Avg Latency (ms)</th><th>Last Sent</th></tr>
  </thead>
  <tbody>
  {metrics_body}
  </tbody>
  </table>
</div>
<script>
const chartData = {chart_data};
function drawChart(limit){{
  const canvas = document.getElementById('phiChart');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  ctx.scale(dpr, dpr);
  const w = rect.width;
  const h = rect.height;
  ctx.clearRect(0, 0, w, h);
  const data = chartData.slice(-limit);
  if (!data.length) return;
  const pad = {{ top: 10, right: 10, bottom: 24, left: 40 }};
  const plotW = w - pad.left - pad.right;
  const plotH = h - pad.top - pad.bottom;
  const values = data.map(d => d.value);
  const min = Math.max(0, Math.min(...values) - 0.05);
  const max = Math.min(1.05, Math.max(...values) + 0.05);
  const xFor = i => pad.left + (i / Math.max(1, data.length - 1)) * plotW;
  const yFor = v => pad.top + plotH - ((v - min) / (max - min || 1)) * plotH;
  ctx.strokeStyle = '#2563eb';
  ctx.lineWidth = 2;
  ctx.beginPath();
  for (let i = 0; i < data.length; i++) {{
    const x = xFor(i);
    const y = yFor(data[i].value);
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  }}
  ctx.stroke();
  ctx.fillStyle = '#2563eb33';
  ctx.beginPath();
  ctx.moveTo(xFor(0), yFor(data[0].value));
  for (let i = 1; i < data.length; i++) ctx.lineTo(xFor(i), yFor(data[i].value));
  ctx.lineTo(xFor(data.length - 1), pad.top + plotH);
  ctx.lineTo(xFor(0), pad.top + plotH);
  ctx.closePath();
  ctx.fill();
  ctx.fillStyle = '#374151';
  ctx.font = '11px Arial';
  ctx.textAlign = 'center';
  for (let i = 0; i < data.length; i += Math.max(1, Math.floor(data.length / 5))) {{
    const x = xFor(i);
    ctx.fillText(new Date(data[i].ts * 1000).toLocaleTimeString(), x, h - 6);
  }}
  ctx.textAlign = 'right';
  ctx.textBaseline = 'middle';
  const steps = 4;
  for (let i = 0; i <= steps; i++) {{
    const v = min + (i / steps) * (max - min);
    const y = yFor(v);
    ctx.fillText(v.toFixed(2), pad.left - 6, y);
    ctx.strokeStyle = '#e5e7eb';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(pad.left, y);
    ctx.lineTo(w - pad.right, y);
    ctx.stroke();
  }}
}}
function setLimit(n){{
  document.querySelectorAll('.controls button').forEach(b => b.classList.remove('active'));
  document.getElementById('btn-' + n).classList.add('active');
  drawChart(n);
}}
function render(payload){{
  const data = payload || {{}};
  const phi = document.getElementById('phi');
  const phiCard = document.querySelector('.card:nth-child(4) .value');
  if (phi) phi.textContent = 'φ-CPS: ' + (data.phi_cps ?? '--') + ' | Updated: ' + (data.timestamp || new Date().toISOString());
  if (phiCard && data.phi_cps !== undefined) phiCard.textContent = parseFloat(data.phi_cps).toFixed(3);
  if (!Array.isArray(data.results)) return;
  const tbody = document.querySelector('tbody');
  if (!tbody) return;
  const map = new Map(data.results.map(r => [r.name, r]));
  let healthy = 0;
  for (const tr of tbody.rows) {{
    const name = tr.children[0].textContent;
    const item = map.get(name);
    if (!item) continue;
    const status = item.status || 'unknown';
    const badge = '<span class=\"badge ' + status + '\">' + status + '</span>';
    tr.children[2].innerHTML = badge;
    tr.children[3].textContent = item.pid || '';
    tr.children[4].textContent = item.last_check || '';
    if (status === 'ok') healthy++;
  }}
  const unhealthyCell = document.querySelector('.card:nth-child(3) .value');
  if (unhealthyCell) unhealthyCell.textContent = data.total - healthy;
  const phiDisplay = document.getElementById('phi');
  if (phiDisplay && data.phi_cps !== undefined) phiDisplay.textContent = 'φ-CPS: ' + parseFloat(data.phi_cps).toFixed(3) + ' | Updated: ' + (data.timestamp || new Date().toISOString());
}}
function connect(){{
  const es = new EventSource('/events');
  es.onmessage = function(e){{
    try {{ render(JSON.parse(e.data)); }} catch {{}}
  }};
  es.onerror = function(){{
    es.close();
    setTimeout(connect, 2000);
  }};
}}
setLimit(20);
connect();
</script>
</body>
</html>
"""
    return html, 200, {"Content-Type": "text/html; charset=utf-8"}

@app.post('/process/release-handles')
@login_required(roles=['admin', 'operator'])
def release_handles() -> Any:
    if not request.is_json:
        return jsonify({'error': 'body_must_be_json'}), 400

    data = request.get_json() or {}
    pid = data.get('pid')
    worktree_path = data.get('worktree_path')
    timeout = int(data.get('timeout', 5))

    if not pid and not worktree_path:
        return jsonify({'error': 'missing_fields', 'details': 'pid or worktree_path is required'}), 400

    released = 0
    details = []
    status = 'released'

    if pid:
        try:
            if sys.platform == 'win32':
                proc = subprocess.run(
                    ['taskkill', '/F', '/T', '/PID', str(pid)],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
                if proc.returncode == 0:
                    released += 1
                    details.append(f'killed_tree_pid={pid}')
                else:
                    details.append(f'taskkill_failed_pid={pid}:{proc.stderr.strip()}')
            else:
                os.kill(pid, 9)
                released += 1
                details.append(f'killed_pid={pid}')
        except subprocess.TimeoutExpired:
            status = 'pending_gc'
            details.append(f'timeout_pid={pid}')
        except OSError as exc:
            details.append(f'kill_error_pid={pid}:{exc}')

    if worktree_path:
        handle_exe = Path(r'C:\Program Files\Sysinternals\handle.exe')
        if not handle_exe.exists():
            handle_exe = Path(r'C:\Program Files (x86)\Sysinternals\handle.exe')
        if handle_exe.exists():
            try:
                args = [str(handle_exe), '-nobanner']
                if pid:
                    args.extend(['-p', str(pid)])
                else:
                    args.append(str(worktree_path))
                proc = subprocess.run(
                    args,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
                stdout = proc.stdout.strip()
                if stdout:
                    details.append(f'handle_scan:{stdout[:200]}')
            except Exception as exc:
                details.append(f'handle_error:{exc}')
        else:
            details.append('handle_exe_not_found')

    if not details:
        details.append('noop')

    AUDIT_LOG.record(
        'release_handles',
        '/process/release-handles',
        'POST',
        getattr(request, 'user', {}).get('sub'),
        details=';'.join(details),
        ip_address=request.remote_addr,
    )

    return jsonify({
        'status': status,
        'pid': pid,
        'worktree_path': worktree_path,
        'released_handles': released,
        'details': details,
    }), 200 if status == 'released' else 202


KIX_PORT = int(os.environ.get("KIX_PORT", "8800"))

if __name__ == '__main__':
    with app.app_context():
        try:
            runners = _load_runners_config()
            # Phase 1 : démarrer les runners bootstrap en priorité
            for spec in runners:
                if spec.bootstrap and spec.auto_start:
                    instance = _get_runner_instance(spec.name)
                    if instance is not None:
                        result = instance.start()
                        status = result.get("status", "starting")
                        pid = result.get("pid")
                        now = _utcnow()
                        STORE.upsert(spec.name, status=status, pid=pid, started_at=now, updated_at=now)
                        print(f"[KIX] bootstrap {spec.name} -> {status} pid={pid}")
            # Phase 2 : démarrer les runners auto_start non-bootstrap
            for spec in runners:
                if spec.auto_start and not spec.bootstrap:
                    instance = _get_runner_instance(spec.name)
                    if instance is not None:
                        result = instance.start()
                        status = result.get("status", "starting")
                        pid = result.get("pid")
                        now = _utcnow()
                        STORE.upsert(spec.name, status=status, pid=pid, started_at=now, updated_at=now)
                        print(f"[KIX] auto_start {spec.name} -> {status} pid={pid}")
        except Exception as exc:
            print(f"[KIX] auto_start failed: {exc}")
    app.run(host='0.0.0.0', port=KIX_PORT, debug=False)
