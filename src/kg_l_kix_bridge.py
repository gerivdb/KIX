"""
KG-L KIX Bridge — Émet des edges KG-L depuis KIX pour les runners et les gardes.

Intégré à KIX pour un fonctionnement en temps réel.
Hooks:
  - runner_state.py après upsert()
  - zombie_monitor.py après détection (déjà présent)
  - immune.py après calcul φ-CPS

Usage:
    from kg_l_kix_bridge import emit_runner_node, emit_prevents_edge
    emit_runner_node("runner-1", status="running", pid=1234, ...)
    emit_prevents_edge("guard:phi-cps", "runner:runner-1", reason="phi_cps_low")
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# WAL NEXUS integration
WAL_DIR = Path(__file__).resolve().parent.parent / ".kilo" / "wal"
KG_L_EDGE_FILE = WAL_DIR / "kg-l-edges.jsonl"

INTENT_HASH = "0xPRD_MOC_IMPL_PLAN_META_LOGIC_UNIFIED_EXECUTION_20260813"


def _ensure_wal_dir() -> None:
    """Crée le répertoire WAL si nécessaire."""
    KG_L_EDGE_FILE.parent.mkdir(parents=True, exist_ok=True)


def emit_edge(src: str, dst: str, kind: str = "causes", metadata: Optional[dict[str, Any]] = None) -> None:
    """
    Émet un edge KG-L vers le fichier WAL partagé.

    Args:
        src: ID source (ex: "runner:name", "guard:phi-cps")
        dst: ID destination (ex: "kg-l:root", "runner:name")
        kind: Type d'edge (causes, prevents, depends_on, governed_by, etc.)
        metadata: Métadonnées supplémentaires
    """
    _ensure_wal_dir()
    edge = {
        "src": src,
        "dst": dst,
        "kind": kind,
        "metadata": metadata or {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "intent_hash": INTENT_HASH,
    }
    with open(KG_L_EDGE_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(edge, ensure_ascii=False) + "\n")


def emit_runner_node(
    name: str,
    status: str = "unknown",
    pid: Optional[int] = None,
    started_at: Optional[str] = None,
    updated_at: Optional[str] = None,
    port: Optional[int] = None,
    **extra_meta: Any,
) -> None:
    """
    Émet un nœud runner + edge causes vers kg-l:root.

    Args:
        name: Nom du runner
        status: Statut (running/stopped/starting/unknown/failed)
        pid: PID du processus
        started_at: Timestamp ISO 8601
        updated_at: Timestamp ISO 8601
        port: Port d'écoute
        **extra_meta: Métadonnées supplémentaires
    """
    runner_id = f"runner:{name}"
    metadata: dict[str, Any] = {
        "status": status,
        "pid": pid,
        "started_at": started_at,
        "updated_at": updated_at,
        "port": port,
        "instance_type": "runner",
    }
    metadata.update(extra_meta)

    emit_edge(runner_id, "kg-l:root", kind="causes", metadata=metadata)


def emit_prevents_edge(
    src: str,
    dst: str,
    reason: str,
    **metadata: Any,
) -> None:
    """
    Émet un edge prevents pour bloquer une instance.

    Args:
        src: ID source (ex: "guard:phi-cps", "guard:zombie-threshold")
        dst: ID destination (ex: "runner:name", "process:1234")
        reason: Raison du blocage
        **metadata: Métadonnées supplémentaires
    """
    meta = {"reason": reason}
    meta.update(metadata)
    emit_edge(src, dst, kind="prevents", metadata=meta)


def state_to_kg_state(kix_status: str) -> str:
    """
    Convertit un statut KIX en état KG-L unifié.

    Args:
        kix_status: Statut KIX (running/stopped/starting/unknown/failed)

    Returns:
        État KG-L unifié (PENDING/RUNNING/STOPPED/KILLED/ERROR)
    """
    mapping = {
        "starting": "PENDING",
        "running": "RUNNING",
        "stopped": "STOPPED",
        "failed": "ERROR",
        "unknown": "PENDING",
    }
    return mapping.get(kix_status.lower(), "PENDING")
