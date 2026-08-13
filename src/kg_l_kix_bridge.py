"""
KIX → KG-L Bridge — P6-2 Intégration temps réelle.

Appelé depuis :
- runner_state.py après upsert()  → emit_runner_node()
- zombie_monitor.py après détection → log_kg_l_edge() (déjà inline)
- immune.py après calcul φ-CPS      → emit_edge()

Usage:
    from kg_l_kix_bridge import emit_runner_node, emit_edge
    emit_runner_node(name="gw-brain", status="running", pid=1234, ...)
    emit_edge(src="korx-sem", dst="kg-l:root", kind="causes", metadata={...})
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

# ── Chemin vers le runtime KG-L (GeriCode) ─────────────────────────────────────

GERICODE_RUNTIME_DIR = Path(
    r"D:\DO\WEB\TOOLS\L2-PLATFORM\GeriCode\.kilo\worktrees\feat-unified-execution-phase6"
    r"\.kilo\skills\kg-l-runtime\runtime"
)

if str(GERICODE_RUNTIME_DIR) not in sys.path:
    sys.path.insert(0, str(GERICODE_RUNTIME_DIR))

# WAL local KIX (prioritaire sur WAL partagé)
WAL_DIR = Path(__file__).resolve().parents[1] / ".kilo" / "wal"
KG_L_EDGE_FILE = WAL_DIR / "kg-l-edges.jsonl"
WAL_DIR.mkdir(parents=True, exist_ok=True)


# ── Helpers ─────────────────────────────────────────────────────────────────────


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append_wal(record: Dict[str, Any]) -> None:
    """Ajoute un enregistrement au WAL KG-L (best-effort)."""
    try:
        with KG_L_EDGE_FILE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": _timestamp(), **record}, ensure_ascii=False) + "\n")
    except Exception:
        pass  # best-effort


def _load_runtime() -> Optional[Any]:
    """
    Tente d'importer le runtime KG-L en mémoire.
    Retourne None si les modules ne sont pas disponibles.
    """
    try:
        from kg_l import KGLRuntime  # noqa: F401

        return KGLRuntime(name="kix-runtime")
    except Exception:
        return None


# ── API publique ───────────────────────────────────────────────────────────────


def emit_runner_node(
    name: str,
    status: str,
    pid: Optional[int] = None,
    started_at: Optional[str] = None,
    updated_at: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Émet un nœud KG-L pour un runner KIX.

    Args:
        name: Nom du runner
        status: Statut (running/stopped/error/...)
        pid: PID du processus (si démarré)
        started_at: Timestamp de démarrage (ISO)
        updated_at: Timestamp de mise à jour (ISO)
        metadata: Métadonnées additionnelles

    Returns:
        Dict avec l'enregistrement WAL émis
    """
    node_id = f"runner:{name}"
    node_meta: Dict[str, Any] = {
        "status": status,
        "pid": pid,
        "started_at": started_at,
        "updated_at": updated_at,
        "instance_type": "runner",
        "source": "kix-bridge",
    }
    if metadata:
        node_meta.update(metadata)

    record = {
        "event": "node_create",
        "node_id": node_id,
        "kind": "runner",
        "metadata": node_meta,
    }
    _append_wal(record)

    # Runtime en mémoire (optionnel)
    runtime = _load_runtime()
    if runtime is not None:
        try:
            from kg_l_kix_adapter import RunnerAdapter  # noqa: F401

            node = RunnerAdapter.add_runner_to_runtime(
                runtime,
                name=name,
                status=status,
                pid=pid,
                started_at=started_at,
                updated_at=updated_at,
            )
            # Edge causes : runner enregistré → runner running (si status=running)
            if status == "running":
                runtime.add_edge(
                    node_id,
                    node_id,
                    kind="causes",
                    metadata={"event": "start", "source": "kix-bridge"},
                )
        except Exception:
            pass  # best-effort

    return record


def emit_edge(
    src: str,
    dst: str,
    kind: str = "causes",
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Émet un edge KG-L générique.

    Args:
        src: ID du nœud source
        dst: ID du nœud destination
        kind: Type d'edge (causes/depends_on/prevents/governed_by/...)
        metadata: Métadonnées additionnelles

    Returns:
        Dict avec l'enregistrement WAL émis
    """
    record = {
        "event": "edge_add",
        "src": src,
        "dst": dst,
        "kind": kind,
        "metadata": metadata or {},
    }
    _append_wal(record)

    # Runtime en mémoire (optionnel)
    runtime = _load_runtime()
    if runtime is not None:
        try:
            runtime.add_edge(src, dst, kind=kind, **(metadata or {}))
        except Exception:
            pass  # best-effort

    return record


def emit_runner_stop(name: str, exit_code: Optional[int] = None) -> Dict[str, Any]:
    """
    Émet un edge causes pour l'arrêt d'un runner.

    Args:
        name: Nom du runner
        exit_code: Code de sortie (si disponible)

    Returns:
        Dict avec l'enregistrement WAL émis
    """
    final_state = "error" if exit_code not in (0, None) else "stopped"
    return emit_edge(
        src=f"runner:{name}",
        dst=f"runner:{name}",
        kind="causes",
        metadata={
            "event": "stop",
            "final_state": final_state,
            "exit_code": exit_code,
            "source": "kix-bridge",
        },
    )


def emit_zombie_prevent(
    pid: int,
    zombie_type: str,
    name: str,
    age_hours: float = 0.0,
) -> Dict[str, Any]:
    """
    Émet un edge prevents pour un processus zombie détecté.

    Args:
        pid: PID du processus zombie
        zombie_type: Type de zombie (git/node/python/...)
        name: Nom du processus
        age_hours: Âge en heures

    Returns:
        Dict avec l'enregistrement WAL émis
    """
    return emit_edge(
        src="guard:zombie-threshold",
        dst=f"process:{pid}",
        kind="prevents",
        metadata={
            "zombie_type": zombie_type,
            "name": name,
            "reason": "process_zombie",
            "age_hours": age_hours,
            "source": "kix-bridge",
        },
    )


# ── CLI (pour tests manuels) ───────────────────────────────────────────────────


def main(argv: Optional[list] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="kg_l_kix_bridge",
        description="KIX → KG-L bridge — émet edges depuis runner_state/zombie_monitor/immune.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # runner-node
    p_node = sub.add_parser("runner-node", help="Émet un nœud runner KG-L")
    p_node.add_argument("name")
    p_node.add_argument("--status", default="running")
    p_node.add_argument("--pid", type=int, default=None)
    p_node.add_argument("--started-at", default=None)
    p_node.add_argument("--updated-at", default=None)

    # edge
    p_edge = sub.add_parser("edge", help="Émet un edge KG-L générique")
    p_edge.add_argument("src")
    p_edge.add_argument("dst")
    p_edge.add_argument("--kind", default="causes")

    args = parser.parse_args(argv)

    if args.command == "runner-node":
        rec = emit_runner_node(
            name=args.name,
            status=args.status,
            pid=args.pid,
            started_at=args.started_at,
            updated_at=args.updated_at,
        )
        print(f"[KIX/KG-L] runner-node emitted: {rec['node_id']}")
    elif args.command == "edge":
        rec = emit_edge(src=args.src, dst=args.dst, kind=args.kind)
        print(f"[KIX/KG-L] edge emitted: {args.src} --{args.kind}-> {args.dst}")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
