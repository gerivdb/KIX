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

app = Flask(__name__)

STORE = RunnerStateStore(os.environ.get("KIX_DB", str(Path(__file__).resolve().parent.parent / "data" / "kix.sqlite")))
NOTIFICATIONS = NotificationStore(os.environ.get("KIX_NOTIFICATIONS_DB", str(Path(__file__).resolve().parent.parent / "data" / "notifications.db")))
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


def _load_phi_cps_history(limit: int = 20) -> list[dict[str, Any]]:
    default_db = Path(__file__).resolve().parent.parent / "data" / "kix.sqlite"
    bridge_db = Path(__file__).resolve().parent.parent / "scripts" / ".." / "L3-CITIZENS" / "MIMIR" / "data" / "metrics.db"
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
    bridge_db = Path(__file__).resolve().parent.parent / "scripts" / ".." / "L3-CITIZENS" / "MIMIR" / "data" / "metrics.db"
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
    history = _load_phi_cps_history(limit=20)
    history_rows = []
    for item in history:
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
    html = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<title>KIX Dashboard</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 2rem; }}
table {{ border-collapse: collapse; width: 100%; margin-bottom: 1.5rem; }}
th, td {{ border: 1px solid #bbb; padding: 0.5rem; text-align: left; }}
.badge.ok {{ color: #fff; background: #2a9d8f; padding: 0.2rem 0.5rem; border-radius: 4px; }}
.badge.stopped {{ color: #fff; background: #e76f51; padding: 0.2rem 0.5rem; border-radius: 4px; }}
.badge.starting {{ color: #fff; background: #e9c46a; padding: 0.2rem 0.5rem; border-radius: 4px; }}
.badge.unknown {{ color: #fff; background: #9ca3af; padding: 0.2rem 0.5rem; border-radius: 4px; }}
.badge.alert-triggered {{ color: #fff; background: #d62828; padding: 0.2rem 0.5rem; border-radius: 4px; }}
.badge.alert-skipped {{ color: #fff; background: #6c757d; padding: 0.2rem 0.5rem; border-radius: 4px; }}
#phi {{ font-size: 1.2rem; margin-bottom: 1rem; }}
</style>
</head>
<body>
<h1>KIX Dashboard</h1>
<p id="phi">φ-CPS: -- | Updated: {_utcnow()}</p>
<table>
<thead>
<tr><th>Name</th><th>Port</th><th>Status</th><th>Pid</th><th>Last check</th></tr>
</thead>
<tbody>
{body}
</tbody>
</table>
<h2>φ-CPS History</h2>
<table>
<thead>
<tr><th>Timestamp</th><th>Value</th></tr>
</thead>
<tbody>
{history_body}
</tbody>
</table>
<h2>Recent Alerts</h2>
<table>
<thead>
<tr><th>Timestamp</th><th>Triggered</th><th>φ-CPS</th><th>Threshold</th><th>Services</th></tr>
</thead>
<tbody>
{alert_body}
</tbody>
</table>
<script>
function render(payload){{
  const data = payload || {{}};
  const phi = document.getElementById('phi');
  if (phi) phi.textContent = 'φ-CPS: ' + (data.phi_cps ?? '--') + ' | Updated: ' + (data.timestamp || new Date().toISOString());
  if (!Array.isArray(data.results)) return;
  const tbody = document.querySelector('tbody');
  if (!tbody) return;
  const map = new Map(data.results.map(r => [r.name, r]));
  const rows = [];
  for (const tr of tbody.rows) {{
    const name = tr.children[0].textContent;
    const item = map.get(name);
    if (!item) continue;
    const status = item.status || 'unknown';
    const badge = '<span class=\"badge ' + status + '\">' + status + '</span>';
    tr.children[2].innerHTML = badge;
    tr.children[3].textContent = item.pid || '';
    tr.children[4].textContent = item.last_check || '';
  }}
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
connect();
</script>
</body>
</html>
"""
    return html, 200, {"Content-Type": "text/html; charset=utf-8"}
