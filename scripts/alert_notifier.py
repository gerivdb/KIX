#!/usr/bin/env python3
"""Phase 12 — Alert notifier for KIX/MIMIR.

Monitors phi-CPS and sends a notification when it stays below threshold
for N consecutive cycles.

Usage:
    python scripts/alert_notifier.py --kix http://localhost:8800 --mimir "D:/DO/WEB/TOOLS/L3-CITIZENS/MIMIR/data/metrics.db" --interval 5 --threshold 0.9 --cycles 3 --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import requests
except ImportError:
    requests = None


DEFAULT_KIX_URL = "http://localhost:8800"
DEFAULT_MIMIR_DB = str(Path(__file__).resolve().parent.parent / "L3-CITIZENS" / "MIMIR" / "data" / "metrics.db")
DEFAULT_INTERVAL = 5
DEFAULT_THRESHOLD = 0.9
DEFAULT_CYCLES = 3


def fetch_alerts(base_url: str, service: str | None = None) -> dict[str, Any]:
    if requests is None:
        raise RuntimeError("requests is required")
    url = f"{base_url}/alerts"
    params = {}
    if service:
        params["service"] = service
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def send_notification(payload: dict[str, Any], webhook_url: str | None) -> None:
    if webhook_url:
        if requests is None:
            raise RuntimeError("requests is required for webhook notifications")
        requests.post(webhook_url, json=payload, timeout=10)
    else:
        print(json.dumps({"notification": payload}, ensure_ascii=False))


def monitor(kix_url: str, mimir_db: str, interval: int, threshold: float, cycles: int, dry_run: bool, webhook_url: str | None, service: str | None = None) -> int:
    consecutive = 0
    print(f"[alert_notifier] Monitoring {kix_url}/alerts | threshold={threshold} | cycles={cycles} | interval={interval}s | dry_run={dry_run}")
    try:
        while True:
            data = fetch_alerts(kix_url, service=service)
            phi_cps = float(data.get("phi_cps", 1.0))
            triggered = bool(data.get("triggered"))
            ts = datetime.fromtimestamp(int(data.get("timestamp", time.time())), tz=timezone.utc).isoformat()
            if triggered:
                consecutive += 1
            else:
                consecutive = 0
            print(f"[alert_notifier] {ts} phi_cps={phi_cps} triggered={triggered} consecutive={consecutive}")
            if consecutive >= cycles:
                payload = {
                    "event": "phi_cps_degraded",
                    "timestamp": ts,
                    "phi_cps": phi_cps,
                    "threshold": threshold,
                    "consecutive_cycles": consecutive,
                    "service": service,
                    "items": data.get("items", []),
                }
                print(json.dumps({"notification": payload}, ensure_ascii=False))
                if not dry_run:
                    send_notification(payload, webhook_url)
                consecutive = 0
            time.sleep(interval)
    except KeyboardInterrupt:
        print("[alert_notifier] Stopped")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="KIX alert notifier")
    parser.add_argument("--kix", default=os.environ.get("KIX_URL", DEFAULT_KIX_URL))
    parser.add_argument("--mimir", default=os.environ.get("MIMIR_DB", DEFAULT_MIMIR_DB))
    parser.add_argument("--interval", type=int, default=int(os.environ.get("ALERT_INTERVAL", DEFAULT_INTERVAL)))
    parser.add_argument("--threshold", type=float, default=float(os.environ.get("ALERT_THRESHOLD", DEFAULT_THRESHOLD)))
    parser.add_argument("--cycles", type=int, default=int(os.environ.get("ALERT_CYCLES", DEFAULT_CYCLES)))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--webhook-url", default=os.environ.get("ALERT_WEBHOOK_URL"))
    parser.add_argument("--service", default=None)
    args = parser.parse_args(argv)
    return monitor(args.kix, args.mimir, args.interval, args.threshold, args.cycles, args.dry_run, args.webhook_url, args.service)


if __name__ == "__main__":
    sys.exit(main())
