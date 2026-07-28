#!/usr/bin/env python3
"""Phase 11 — KIX/MIMIR pipeline health check."""

import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

KIX_URL = "http://localhost:8800"
MIMIR_DB = Path(r"D:\DO\WEB\TOOLS\L3-CITIZENS\MIMIR\data\metrics.db")


def check_kix() -> bool:
    try:
        import urllib.request
        with urllib.request.urlopen(f"{KIX_URL}/health", timeout=10) as r:
            return r.status == 200
    except Exception:
        return False


def check_mimir() -> dict:
    if not MIMIR_DB.exists():
        return {"ok": False, "error": f"missing {MIMIR_DB}"}
    try:
        conn = sqlite3.connect(MIMIR_DB)
        conn.row_factory = sqlite3.Row
        phi = conn.execute("SELECT COUNT(*) as cnt FROM phi_cps").fetchone()
        health = conn.execute("SELECT COUNT(*) as cnt FROM health").fetchone()
        alerts = conn.execute("SELECT COUNT(*) as cnt FROM alerts").fetchone()
        latest = conn.execute("SELECT ts, value FROM phi_cps ORDER BY ts DESC LIMIT 1").fetchone()
        conn.close()
        return {
            "ok": True,
            "phi_cps_rows": phi["cnt"],
            "health_rows": health["cnt"],
            "alert_rows": alerts["cnt"],
            "latest_phi_cps": latest["value"] if latest else None,
            "latest_ts": datetime.fromtimestamp(latest["ts"], tz=timezone.utc).isoformat() if latest else None,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def main() -> int:
    print("[Phase 11] KIX/MIMIR pipeline health check")
    print(f"  KIX URL : {KIX_URL}")
    print(f"  MIMIR DB: {MIMIR_DB}")
    kix_ok = check_kix()
    print(f"  KIX /health: {'OK' if kix_ok else 'DOWN'}")
    mimir = check_mimir()
    if mimir.get("ok"):
        print(f"  MIMIR phi_cps rows : {mimir['phi_cps_rows']}")
        print(f"  MIMIR health rows  : {mimir['health_rows']}")
        print(f"  MIMIR alert rows   : {mimir['alert_rows']}")
        print(f"  Latest phi_cps     : {mimir['latest_phi_cps']} ({mimir['latest_ts']})")
    else:
        print(f"  MIMIR: ERROR - {mimir.get('error')}")
    if kix_ok and mimir.get("ok"):
        print("[Phase 11] Pipeline: HEALTHY")
        return 0
    print("[Phase 11] Pipeline: DEGRADED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
