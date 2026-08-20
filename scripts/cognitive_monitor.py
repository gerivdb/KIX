"""Monitoring du Conversation Cognitive Runner.

Surveille l'état du runner conversation-cognitive (port 8811) et génère
des alertes en cas d'échec. Utilisable en tant que script standalone ou
intégré dans KIX/ECOS.

Métriques surveillées :
- Health check /cognitive/conversation/health
- Taille de cognitive_decisions.json
- Présence de l'endpoint /cognitive/decisions
- Présence de l'endpoint /cognitive/phi (optionnel)
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

KIX_DIR = Path(__file__).resolve().parent.parent
COGNITIVE_URL = "http://127.0.0.1:8811"
DECISIONS_FILE = KIX_DIR / "data" / "cognitive" / "cognitive_decisions.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [COG-MONITOR] %(message)s")
logger = logging.getLogger("cognitive-monitor")

ALERT_THRESHOLD_DECISIONS_SIZE_BYTES = 50 * 1024 * 1024  # 50 Mo
WARN_THRESHOLD_DECISIONS_SIZE_BYTES = 10 * 1024 * 1024   # 10 Mo


def check_health() -> dict[str, Any]:
    """Vérifie le health check du runner."""
    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "runner": "conversation-cognitive",
        "port": 8811,
        "health_ok": False,
        "decisions_ok": False,
        "phi_ok": False,
        "decisions_count": 0,
        "decisions_file_size_bytes": 0,
        "alert": None,
        "details": {},
    }

    # Health check principal
    try:
        resp = requests.get(f"{COGNITIVE_URL}/cognitive/conversation/health", timeout=5)
        result["health_ok"] = resp.status_code == 200
        result["details"]["health_status"] = resp.status_code
        if resp.status_code == 200:
            result["details"]["health_body"] = resp.json()
    except Exception as exc:
        result["alert"] = f"Runner inaccessible: {exc}"
        return result

    if not result["health_ok"]:
        result["alert"] = "Health check non-200"
        return result

    # Vérifier endpoint /cognitive/decisions
    try:
        resp = requests.get(f"{COGNITIVE_URL}/cognitive/decisions", timeout=5)
        result["decisions_ok"] = resp.status_code == 200
        if resp.status_code == 200:
            data = resp.json()
            result["decisions_count"] = data.get("count", 0)
    except Exception as exc:
        result["alert"] = f"Endpoint /cognitive/decisions inaccessible: {exc}"
        return result

    # Vérifier endpoint /cognitive/phi (optionnel)
    try:
        resp = requests.get(f"{COGNITIVE_URL}/cognitive/phi", timeout=5)
        result["phi_ok"] = resp.status_code == 200
        if resp.status_code == 200:
            result["details"]["phi"] = resp.json()
    except Exception:
        result["phi_ok"] = False
        result["details"]["phi_note"] = "Endpoint /cognitive/phi non disponible"

    # Vérifier taille du fichier local
    if DECISIONS_FILE.exists():
        size = DECISIONS_FILE.stat().st_size
        result["decisions_file_size_bytes"] = size
        if size > ALERT_THRESHOLD_DECISIONS_SIZE_BYTES:
            result["alert"] = f"cognitive_decisions.json trop volumineux: {size / 1024 / 1024:.1f} Mo"
        elif size > WARN_THRESHOLD_DECISIONS_SIZE_BYTES:
            result["details"]["size_warn"] = f"{size / 1024 / 1024:.1f} Mo"

    return result


def main() -> int:
    """Point d'entrée principal."""
    report = check_health()

    # Logging structuré
    if report["alert"]:
        logger.warning("ALERT: %s", report["alert"])
    else:
        logger.info(
            "OK: health=%s decisions=%s count=%s phi=%s",
            report["health_ok"],
            report["decisions_ok"],
            report["decisions_count"],
            report["phi_ok"],
        )

    # Sortie JSON pour intégration CI
    print(json.dumps(report, ensure_ascii=False, indent=2))

    return 1 if report["alert"] else 0


if __name__ == "__main__":
    sys.exit(main())
