#!/usr/bin/env python3
"""
KG-L KIX Bridge — Pont temps réel entre KIX Runner et KG-L.

Ce bridge est appelé depuis KIX après:
- runner_state.upsert() : création/modification runner
- zombie_monitor.detect_zombies() : détection zombies
- immune.py calcul φ-CPS : métriques KORX-L1

Usage:
    from kg_l_kix_bridge import KIXBridge
    bridge = KIXBridge()
    bridge.emit_runner_started(name, pid, port)
    bridge.emit_zombie_detected(pid, name)
    bridge.emit_phi_cps_update(phi_cps)
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Runtime KG-L — try multiple paths for cross-repo compatibility
_RUNTIME_DIR = Path(__file__).resolve().parents[2] / ".kilo" / "skills" / "kg-l-runtime" / "runtime"
_ALT_RUNTIME_DIR = Path(__file__).resolve().parent.parent / ".kilo" / "skills" / "kg-l-runtime" / "runtime"
_GERICODE_RUNTIME = Path(r"D:\DO\WEB\TOOLS\L2-PLATFORM\GeriCode\.kilo\skills\kg-l-runtime\runtime")
if _RUNTIME_DIR.exists():
    sys.path.insert(0, str(_RUNTIME_DIR))
elif _ALT_RUNTIME_DIR.exists():
    sys.path.insert(0, str(_ALT_RUNTIME_DIR))
elif _GERICODE_RUNTIME.exists():
    sys.path.insert(0, str(_GERICODE_RUNTIME))

from kg_l import KGLRuntime, KGNode, KGEdge  # noqa: E402


class KIXBridge:
    """Pont temps réel KIX -> KG-L."""

    def __init__(self, runtime: Optional[KGLRuntime] = None) -> None:
        self.runtime = runtime or KGLRuntime(name="kix-live")
        self._edge_log_path = Path(__file__).resolve().parent.parent / ".kilo" / "wal" / "kg-l-edges.jsonl"
        self._edge_log_path.parent.mkdir(parents=True, exist_ok=True)

    def emit_runner_started(
        self,
        name: str,
        pid: Optional[int] = None,
        port: Optional[int] = None,
        status: str = "running",
    ) -> KGNode:
        """
        Émet un nœud runner + edge lors du démarrage.

        Args:
            name: Nom du runner
            pid: PID du processus
            port: Port d'écoute
            status: Statut initial

        Returns:
            KGNode créé
        """
        node = KGNode(
            id=f"runner:{name}",
            kind="runner",
            metadata={
                "status": status,
                "pid": pid,
                "port": port,
                "started_at": self._utcnow_iso(),
                "instance_type": "runner",
            },
        )
        self.runtime.add_node(node.id, kind=node.kind, **node.metadata)

        edge = KGEdge(
            src=f"runner:{name}:start",
            dst=f"runner:{name}",
            kind="causes",
            metadata={"event": "runner_started", "pid": pid, "port": port, "timestamp": self._utcnow_iso()},
        )
        self.runtime.add_edge(edge.src, edge.dst, kind=edge.kind, **edge.metadata)
        self._log_edge(edge)
        return node

    def emit_runner_stopped(self, name: str) -> None:
        """Émet la transition RUNNING -> STOPPED."""
        runner_id = f"runner:{name}"
        if runner_id in self.runtime.graph.nodes:
            self.runtime.graph.nodes[runner_id].metadata["status"] = "stopped"

        edge = KGEdge(
            src=f"runner:{name}:stop",
            dst=runner_id,
            kind="causes",
            metadata={"event": "runner_stopped", "timestamp": self._utcnow_iso()},
        )
        self.runtime.add_edge(edge.src, edge.dst, kind=edge.kind, **edge.metadata)
        self._log_edge(edge)

    def emit_zombie_detected(
        self,
        pid: int,
        name: str,
        age_hours: float = 0.0,
        zombie_type: str = "process",
    ) -> None:
        """
        Émet un edge prevents pour un zombie détecté.

        Args:
            pid: PID du processus zombie
            name: Nom du runner/processus
            age_hours: Âge en heures
            zombie_type: Type de zombie
        """
        dst = f"process:{pid}" if zombie_type == "process" else f"worktree:{name}"
        edge = KGEdge(
            src="guard:zombie-threshold",
            dst=dst,
            kind="prevents",
            metadata={
                "reason": "zombie",
                "zombie_type": zombie_type,
                "name": name,
                "pid": pid,
                "age_hours": age_hours,
                "timestamp": self._utcnow_iso(),
            },
        )
        self.runtime.add_edge(edge.src, edge.dst, kind=edge.kind, **edge.metadata)
        self._log_edge(edge)

    def emit_phi_cps_update(self, phi_cps: float, soma_metrics: Optional[dict[str, Any]] = None) -> None:
        """
        Émet un nœud métrique pour φ-CPS.

        Args:
            phi_cps: Score φ-CPS actuel
            soma_metrics: Métriques SOMA associées
        """
        metric_id = "soma:phi_cps"
        metadata: dict[str, Any] = {
            "phi_cps": phi_cps,
            "timestamp": self._utcnow_iso(),
            "instance_type": "metric",
        }
        if soma_metrics:
            metadata["soma_metrics"] = soma_metrics

        self.runtime.add_node(metric_id, kind="metric", **metadata)

        edge = KGEdge(
            src="kix:immune",
            dst=metric_id,
            kind="causes",
            metadata={"event": "phi_cps_update", "phi_cps": phi_cps, "timestamp": self._utcnow_iso()},
        )
        self.runtime.add_edge(edge.src, edge.dst, kind=edge.kind, **edge.metadata)
        self._log_edge(edge)

    def _log_edge(self, edge: KGEdge) -> None:
        """Log l'edge dans le WAL KG-L."""
        try:
            record = {
                "src": edge.src,
                "dst": edge.dst,
                "kind": edge.kind,
                "metadata": edge.metadata,
                "timestamp": self._utcnow_iso(),
                "intent_hash": "0xPRD_MOC_META_LOGIC_UNIFIED_EXECUTION_20260813",
            }
            with open(self._edge_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception:
            pass

    @staticmethod
    def _utcnow_iso() -> str:
        return datetime.now(timezone.utc).isoformat()


# Aliases de compatibilité pour les callers existants
def emit_runner_node(
    name: str,
    status: str = "unknown",
    pid: Optional[int] = None,
    started_at: Optional[str] = None,
    updated_at: Optional[str] = None,
    port: Optional[int] = None,
) -> None:
    """Alias compat: emit_runner_node -> emit_runner_started."""
    bridge = KIXBridge()
    bridge.emit_runner_started(name=name, status=status, pid=pid, port=port)


def emit_edge(src: str, dst: str, kind: str = "causes", metadata: Optional[dict[str, Any]] = None) -> None:
    """Alias compat: emit_edge -> emit_phi_cps_update or generic edge."""
    bridge = KIXBridge()
    if kind == "prevents":
        # Generic prevents edge
        edge = KGEdge(src=src, dst=dst, kind=kind, metadata=metadata or {})
        bridge.runtime.add_edge(src, dst, kind=kind, **(metadata or {}))
        try:
            record = {
                "src": src,
                "dst": dst,
                "kind": kind,
                "metadata": metadata or {},
                "timestamp": KIXBridge._utcnow_iso(),
                "intent_hash": "0xPRD_MOC_META_LOGIC_UNIFIED_EXECUTION_20260813",
            }
            with open(bridge._edge_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception:
            pass
    else:
        # Default: treat as phi_cps_update-like event
        bridge.emit_phi_cps_update(phi_cps=0.0, soma_metrics=metadata)
