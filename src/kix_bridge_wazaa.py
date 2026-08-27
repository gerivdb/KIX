#!/usr/bin/env python3
"""
KIX Bridge WAZAA — Remplacement WAZAA du pont direct kg_l_kix_bridge.py.

Publie les événements KIX (runner lifecycle, zombie detection, φ-CPS) sur le
bus WAZAA via KixPublisher. Le WazaaKGSubscriber convertit ces messages en
KGNode/KGEdge dans le runtime KG-L.

Maintient l'interface compat de kg_l_kix_bridge.KIXBridge pour migration
sans rupture :
    - emit_runner_started(name, pid, port, status)
    - emit_runner_stopped(name)
    - emit_zombie_detected(pid, name, age_hours, zombie_type)
    - emit_phi_cps_update(phi_cps, soma_metrics)

Usage:
    from kix_bridge_wazaa import KIXBridge
    bridge = KIXBridge()
    bridge.emit_runner_started(name="trixd", pid=1234, port=8742)
    bridge.emit_zombie_detected(pid=5678, name="zigzag", age_hours=2.5)
    bridge.emit_phi_cps_update(phi_cps=0.94)
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Optional

# Ajoute le repo WAZAA au path pour importer KixPublisher
_WAZAA_SRC = Path(r"D:\DO/WEB\TOOLS\L4-TOOLS\WAZAA\src")
if str(_WAZAA_SRC) not in sys.path:
    sys.path.insert(0, str(_WAZAA_SRC))

from publishers.kix_publisher import KixPublisher  # noqa: E402

logger = logging.getLogger("kix.bridge_wazaa")


class KIXBridge:
    """Pont KIX → WAZAA (remplace le pont direct KG-L).

    Toutes les méthodes emit_* publient sur le bus WAZAA au lieu d'appeler
    kg_l.KGLRuntime directement.
    """

    def __init__(self, publisher: Optional[KixPublisher] = None) -> None:
        self._publisher = publisher or KixPublisher()

    def emit_runner_started(
        self,
        name: str,
        pid: Optional[int] = None,
        port: Optional[int] = None,
        status: str = "running",
    ) -> None:
        """
        Publie un événement de lancement de runner sur WAZAA.
        """
        message = {
            "event": "runner_started",
            "name": name,
            "pid": pid,
            "port": port,
            "status": status,
        }
        self._publisher.publish(message, "kix_runner")
        logger.info("KIX runner %s started (pid=%s, port=%s)", name, pid, port)

    def emit_runner_stopped(self, name: str) -> None:
        """Publie l'événement d'arrêt de runner."""
        message = {
            "event": "runner_stopped",
            "name": name,
        }
        self._publisher.publish(message, "kix_runner")
        logger.info("KIX runner %s stopped", name)

    def emit_zombie_detected(
        self,
        pid: int,
        name: str,
        age_hours: float = 0.0,
        zombie_type: str = "process",
    ) -> None:
        """Publie un événement de zombie détecté."""
        message = {
            "pid": pid,
            "name": name,
            "age_hours": age_hours,
            "zombie_type": zombie_type,
        }
        self._publisher.publish(message, "kix_zombie")
        logger.warning("KIX zombie detected: pid=%d, name=%s, age=%.1fh", pid, name, age_hours)

    def emit_phi_cps_update(
        self,
        phi_cps: float,
        soma_metrics: Optional[dict[str, Any]] = None,
    ) -> None:
        """Publie une mise à jour φ-CPS."""
        message = {
            "phi_cps": phi_cps,
            "soma_metrics": soma_metrics or {},
        }
        self._publisher.publish(message, "kix_phi_cps")
        logger.info("KIX φ-CPS update: %.4f", phi_cps)


# ── Aliases de compatibilité (compat avec kg_l_kix_bridge.py) ─────────────

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


def emit_edge(
    src: str,
    dst: str,
    kind: str = "causes",
    metadata: Optional[dict[str, Any]] = None,
) -> None:
    """Alias compat: émet un edge générique sur WAZAA.

    Pour les edges génériques non couverts par KIX topics, on publie
    sur kix_phi_cps avec les métadonnées de l'edge.
    """
    bridge = KIXBridge()
    bridge.emit_phi_cps_update(
        phi_cps=0.0,
        soma_metrics={"edge": {"src": src, "dst": dst, "kind": kind, **(metadata or {})}},
    )
