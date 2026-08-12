"""KIX Zombie Monitor — Process zombie detection, purge, and cross-repo conflict detection.
IntentHash: 0xPRD_MOC_PROCESS_ZOMBIE_HYGIENE_DEVTOOLS_20260809
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from flask import Blueprint, jsonify, request

zombie_bp = Blueprint("zombie_monitor", __name__, url_prefix="/health")

# WAL NEXUS integration
WAL_DIR = Path(__file__).resolve().parent.parent / ".kilo" / "wal"
WAL_FILE = WAL_DIR / "zombie-monitor.jsonl"
KG_L_EDGE_FILE = WAL_DIR / "kg-l-edges.jsonl"


def log_kg_l_edge(src: str, dst: str, kind: str = "prevents", metadata: Optional[dict[str, Any]] = None) -> None:
    """Émet un edge KG-L pour le graphe unifié d'exécution."""
    KG_L_EDGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    edge = {
        "src": src,
        "dst": dst,
        "kind": kind,
        "metadata": metadata or {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "intent_hash": "0xPRD_MOC_META_LOGIC_UNIFIED_EXECUTION_20260813",
    }
    with open(KG_L_EDGE_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(edge, ensure_ascii=False) + "\n")


def log_wal(event_type: str, data: dict[str, Any]) -> None:
    """Logger un événement de purge dans NEXUS/WAL."""
    WAL_DIR.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "intent_hash": "0xPRD_MOC_PROCESS_ZOMBIE_HYGIENE_DEVTOOLS_20260809",
        "data": data,
    }
    with open(WAL_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


# ═══════════════════════════════════════════════════════════════════════
# Process zombie detection
# ═══════════════════════════════════════════════════════════════════════

_ZOMBIE_PROCESS_NAMES = [
    "git",
    "node",
    "python",
    "zig",
    "cargo",
    "bun",
    "pwsh",
    "trixd",
    "kix",
]


def _is_process_zombie(proc: Any, now: datetime) -> bool:
    """Vérifier si un processus est un zombie selon les critères ENV2."""
    try:
        start_time = proc.StartTime
    except (AttributeError, TypeError):
        return False
    if start_time is None:
        return False
    age_hours = (now - start_time).total_seconds() / 3600
    try:
        memory_mb = proc.WorkingSet64 / (1024 * 1024)
    except (AttributeError, TypeError):
        memory_mb = 0
    main_window_title = getattr(proc, "MainWindowTitle", "") or ""
    cpu = getattr(proc, "CPU", 0) or 0
    return (
        main_window_title == ""
        and cpu < 0.5
        and memory_mb < 10
        and age_hours > 1
    )


def get_process_zombies() -> list[dict[str, Any]]:
    """Inventaire des processus zombies."""
    now = datetime.now()
    zombies: list[dict[str, Any]] = []
    if sys.platform != "win32":
        return zombies

    try:
        import psutil  # type: ignore
    except ImportError:
        # Fallback sans psutil : Win32_Process via wmi
        try:
            import wmi  # type: ignore
            c = wmi.WMI()
            for proc in c.Win32_Process():
                try:
                    name = proc.Name or ""
                    if not any(name.lower().startswith(p) for p in _ZOMBIE_PROCESS_NAMES):
                        continue
                    pid = int(proc.ProcessId)
                    # Approximation : on ne peut pas évaluer CPU/MainWindow sans psutil
                    # On marque comme suspect si CreationDate > 1h
                    creation = proc.CreationDate
                    if creation:
                        cdate = datetime.strptime(creation.split(".")[0], "%Y%m%d%H%M%S")
                        age_hours = (now - cdate).total_seconds() / 3600
                        if age_hours > 1:
                            zombies.append({
                                "pid": pid,
                                "name": name,
                                "type": _guess_type(name),
                                "start_time": cdate.isoformat(),
                                "age_hours": round(age_hours, 1),
                                "cpu": 0.0,
                                "memory_mb": 0.0,
                                "main_window_title": "",
                                "note": "approximated via WMI",
                            })
                except Exception:
                    continue
        except ImportError:
            pass
        return zombies

    for proc in psutil.process_iter(["pid", "name", "create_time", "cpu_percent", "memory_info"]):
        try:
            name = proc.info["name"] or ""
            if not any(name.lower().startswith(p) for p in _ZOMBIE_PROCESS_NAMES):
                continue
            p = psutil.Process(proc.info["pid"])
            start_time = datetime.fromtimestamp(proc.info["create_time"], tz=timezone.utc).replace(tzinfo=None)
            if _is_process_zombie(p, now):
                zombies.append({
                    "pid": proc.info["pid"],
                    "name": name,
                    "type": _guess_type(name),
                    "start_time": start_time.isoformat(),
                    "age_hours": round((now - start_time).total_seconds() / 3600, 1),
                    "cpu": round(proc.info["cpu_percent"] or 0, 2),
                    "memory_mb": round((proc.info["memory_info"].rss / (1024 * 1024)) if proc.info["memory_info"] else 0, 1),
                    "main_window_title": "",
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
            continue
    return zombies


def _guess_type(name: str) -> str:
    lower = name.lower()
    for t in _ZOMBIE_PROCESS_NAMES:
        if lower.startswith(t):
            return t
    return "unknown"


# ═══════════════════════════════════════════════════════════════════════
# Worktree zombie detection
# ═══════════════════════════════════════════════════════════════════════

def get_worktree_zombies() -> list[dict[str, Any]]:
    """Inventaire des worktrees orphelins."""
    zombies: list[dict[str, Any]] = []
    try:
        result = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return zombies
        current_path: Optional[str] = None
        current_branch: Optional[str] = None
        for line in result.stdout.splitlines():
            if line.startswith("worktree "):
                current_path = line.split(" ", 1)[1]
                current_branch = None
            elif line.startswith("HEAD "):
                pass
            elif line.startswith("branch "):
                current_branch = line.split(" ", 1)[1]
        if current_path and current_branch:
            # Vérifier que la branche existe toujours
            branch_check = subprocess.run(
                ["git", "branch", "--list", current_branch],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if branch_check.returncode != 0 or not branch_check.stdout.strip():
                zombies.append({
                    "path": current_path,
                    "branch": current_branch,
                    "reason": "branch_deleted",
                })
    except Exception:
        pass
    return zombies


# ═══════════════════════════════════════════════════════════════════════
# Stash zombie detection
# ═══════════════════════════════════════════════════════════════════════

def get_stash_zombies() -> list[dict[str, Any]]:
    """Inventaire des stashes temporaires anciens."""
    zombies: list[dict[str, Any]] = []
    try:
        result = subprocess.run(
            ["git", "stash", "list", "--format=%gd %ci %s"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return zombies
        now = datetime.now()
        for line in result.stdout.splitlines():
            parts = line.split(" ", 3)
            if len(parts) < 4:
                continue
            stash_id, stash_date_str, stash_msg = parts[0], parts[1], parts[3]
            try:
                stash_date = datetime.strptime(stash_date_str, "%Y-%m-%d %H:%M:%S %z")
                age_days = (now - stash_date).total_seconds() / 86400
            except ValueError:
                continue
            is_temp = any(k in stash_msg.lower() for k in ["temp", "wip", "wrong branch", "before switch"])
            if age_days > 7 or is_temp:
                zombies.append({
                    "stash_id": stash_id,
                    "message": stash_msg,
                    "age_days": round(age_days, 1),
                    "reason": "old" if age_days > 7 else "temporary",
                })
    except Exception:
        pass
    return zombies


# ═══════════════════════════════════════════════════════════════════════
# Cross-repo conflict detection
# ═══════════════════════════════════════════════════════════════════════

def detect_conflicts() -> list[dict[str, Any]]:
    """Détecter les conflits cross-repo (chemins chevauchés, worktrees partagés)."""
    conflicts: list[dict[str, Any]] = []
    # Placeholder: dans un environnement complet, croiser known_repositories.yaml
    # avec les worktrees actifs pour détecter les chemins partagés.
    return conflicts


# ═══════════════════════════════════════════════════════════════════════
# Purge orchestrée
# ═══════════════════════════════════════════════════════════════════════

def purge_zombies(
    types: Optional[list[str]] = None,
    repo: Optional[str] = None,
    worktree: Optional[str] = None,
    priority: str = "high",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Purge orchestrée des zombies par type/repo/worktree/priorité."""
    if types is None:
        types = []
    purged: list[dict[str, Any]] = []
    errors: list[str] = []

    # Purge processus
    if not types or any(t in _ZOMBIE_PROCESS_NAMES for t in types):
        procs = get_process_zombies()
        for z in procs:
            if types and z["type"] not in types:
                continue
            if dry_run:
                purged.append({"type": z["type"], "pid": z["pid"], "name": z["name"], "action": "would_stop"})
            else:
                try:
                    if sys.platform == "win32":
                        subprocess.run(
                            ["taskkill", "/F", "/PID", str(z["pid"])],
                            capture_output=True,
                            timeout=5,
                        )
                        purged.append({"type": z["type"], "pid": z["pid"], "name": z["name"], "action": "stopped"})
                    else:
                        os.kill(z["pid"], 9)
                        purged.append({"type": z["type"], "pid": z["pid"], "name": z["name"], "action": "killed"})
                except Exception as exc:
                    errors.append(f"Failed to stop {z['name']}[{z['pid']}]: {exc}")

    # Purge worktrees
    if not types or "worktree" in types:
        wts = get_worktree_zombies()
        for w in wts:
            if dry_run:
                purged.append({"type": "worktree", "path": w["path"], "action": "would_remove"})
            else:
                try:
                    subprocess.run(
                        ["git", "worktree", "remove", w["path"]],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    purged.append({"type": "worktree", "path": w["path"], "action": "removed"})
                except Exception as exc:
                    errors.append(f"Failed to remove worktree {w['path']}: {exc}")

    # Log WAL
    log_wal(
        "process_zombie_purge",
        {
            "purged": purged,
            "errors": errors,
            "dry_run": dry_run,
            "types_filter": types,
            "repo": repo,
            "worktree": worktree,
            "priority": priority,
        },
    )

    # Emit KG-L edges for zombies
    for z in purged:
        if z.get("type") in _ZOMBIE_PROCESS_NAMES:
            log_kg_l_edge(
                src="guard:zombie-threshold",
                dst=f"process:{z['pid']}",
                kind="prevents",
                metadata={
                    "zombie_type": z["type"],
                    "name": z["name"],
                    "action": z["action"],
                    "reason": "process_zombie",
                },
            )
        elif z.get("type") == "worktree":
            log_kg_l_edge(
                src="guard:worktree-hygiene",
                dst=f"worktree:{z['path']}",
                kind="prevents",
                metadata={
                    "action": z["action"],
                    "reason": "worktree_zombie",
                },
            )

    return {
        "status": "purged" if not dry_run else "dry_run",
        "purged": purged,
        "errors": errors,
        "wal_logged": True,
    }


# ═══════════════════════════════════════════════════════════════════════
# Routes
# ═══════════════════════════════════════════════════════════════════════

@zombie_bp.route("/zombies", methods=["GET"])
def list_zombies() -> Any:
    """GET /health/zombies — Inventaire des zombies par type/repo/worktree."""
    process_zombies = get_process_zombies()
    worktree_zombies = get_worktree_zombies()
    stash_zombies = get_stash_zombies()
    summary: dict[str, int] = {}
    for z in process_zombies:
        t = z.get("type", "unknown")
        summary[t] = summary.get(t, 0) + 1
    for z in worktree_zombies:
        summary["worktree"] = summary.get("worktree", 0) + 1
    for z in stash_zombies:
        summary["stash"] = summary.get("stash", 0) + 1

    return jsonify({
        "service": "kix",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "process_zombies": process_zombies,
        "worktree_zombies": worktree_zombies,
        "stash_zombies": stash_zombies,
        "summary": {
            "total": len(process_zombies) + len(worktree_zombies) + len(stash_zombies),
            "by_type": summary,
        },
    })


@zombie_bp.route("/zombies/purge", methods=["POST"])
def purge_zombies_endpoint() -> Any:
    """POST /health/zombies/purge — Purge orchestrée par type/repo/worktree/priorité."""
    data = request.get_json() or {}
    types = data.get("types")
    repo = data.get("repo")
    worktree = data.get("worktree")
    priority = data.get("priority", "high")
    dry_run = data.get("dry_run", True)

    if not isinstance(types, list):
        types = None

    result = purge_zombies(
        types=types,
        repo=repo,
        worktree=worktree,
        priority=priority,
        dry_run=dry_run,
    )
    return jsonify(result)


@zombie_bp.route("/conflicts", methods=["GET"])
def list_conflicts() -> Any:
    """GET /health/conflicts — Détection de conflits cross-repo."""
    conflicts = detect_conflicts()
    return jsonify({
        "service": "kix",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "conflicts": conflicts,
        "total": len(conflicts),
    })
