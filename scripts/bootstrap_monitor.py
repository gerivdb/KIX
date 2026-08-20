"""Monitoring d'alerte pour le bootstrap runner.

Surveille l'état de bootstrap et génère des alertes en cas d'échec.
Utilisable en tant que script standalone ou intégré dans KIX.
"""

import os
import sys
import json
import time
import logging
import requests
from datetime import datetime, timezone
from pathlib import Path

KIX_DIR = Path(__file__).resolve().parent.parent
BOOTSTRAP_URL = "http://127.0.0.1:8810"
KIX_URL = "http://127.0.0.1:8800"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [BOOTSTRAP-MONITOR] %(message)s")
logger = logging.getLogger("bootstrap-monitor")


def check_bootstrap() -> dict:
    """Vérifie l'état de bootstrap et retourne un rapport."""
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "bootstrap_ok": False,
        "kix_ok": False,
        "alert": None,
        "services": {},
        "blockers": [],
    }

    # Vérifier KIX
    try:
        resp = requests.get(f"{KIX_URL}/health", timeout=2)
        report["kix_ok"] = resp.status_code == 200
    except Exception as exc:
        report["alert"] = f"KIX inaccessible: {exc}"
        return report

    # Vérifier bootstrap
    try:
        resp = requests.get(f"{BOOTSTRAP_URL}/bootstrap/status", timeout=2)
        if resp.status_code == 200:
            data = resp.json()
            report["bootstrap_ok"] = data.get("ready", False)
            report["services"] = data.get("services", {})
            report["blockers"] = data.get("blockers", [])
            if not report["bootstrap_ok"]:
                report["alert"] = f"bootstrap pas pret: {report['blockers']}"
        else:
            report["alert"] = f"bootstrap /bootstrap/status HTTP {resp.status_code}"
    except Exception as exc:
        report["alert"] = f"bootstrap inaccessible: {exc}"

    return report


def monitor_once() -> int:
    """Effectue une vérification unique et retourne le code de sortie."""
    report = check_bootstrap()

    if report["alert"]:
        logger.warning("ALERTE: %s", report["alert"])
        return 1

    logger.info("OK: bootstrap pret, %d services verifies", len(report["services"]))
    return 0


def monitor_loop(interval: int = 30) -> None:
    """Boucle de monitoring continue."""
    logger.info("Demarrage du monitoring (intervalle: %ds)", interval)
    consecutive_failures = 0

    while True:
        try:
            code = monitor_once()
            if code != 0:
                consecutive_failures += 1
                logger.warning("Echec consecutif #%d", consecutive_failures)
            else:
                consecutive_failures = 0
        except Exception as exc:
            logger.error("Erreur dans la boucle de monitoring: %s", exc)
            consecutive_failures += 1

        time.sleep(interval)


def main() -> int:
    """Point d'entrée du script de monitoring."""
    import argparse

    parser = argparse.ArgumentParser(description="Monitoring d'alerte bootstrap")
    parser.add_argument("--interval", type=int, default=30, help="Intervalle de vérification en secondes")
    parser.add_argument("--loop", action="store_true", help="Boucle continue")
    args = parser.parse_args()

    if args.loop:
        monitor_loop(args.interval)
        return 0

    return monitor_once()


if __name__ == "__main__":
    sys.exit(main())
