#!/usr/bin/env python3
"""
KIX → MIMIR Bridge — Poll KIX /probe/audit, store phi_cps and health in MIMIR SQLite.

Usage:
    python scripts/kix_mimir_bridge.py --kix http://localhost:8800 --mimir D:/DO/WEB/TOOLS/L3-CITIZENS/MIMIR/data/metrics.db --interval 5
"""

import argparse
import json
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    raise SystemExit("requests is required: pip install requests")


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def utcnow_ts() -> int:
    return int(time.time())


def fetch_kix_audit(base_url: str) -> dict:
    resp = requests.get(f"{base_url}/probe/audit", timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_kix_alerts(base_url: str) -> dict:
    resp = requests.get(f"{base_url}/alerts", timeout=30)
    resp.raise_for_status()
    return resp.json()


def ensure_schema(conn: sqlite3.Connection):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS health (
            ts INTEGER, runner TEXT, status TEXT, latency_ms INTEGER,
            ternary_role TEXT, version TEXT,
            PRIMARY KEY (ts, runner)
        );
        CREATE TABLE IF NOT EXISTS phi_cps (
            ts INTEGER, value REAL, components TEXT,
            PRIMARY KEY (ts)
        );
        CREATE TABLE IF NOT EXISTS alerts (
            ts INTEGER, triggered INTEGER, phi_cps REAL, threshold REAL,
            payload TEXT,
            PRIMARY KEY (ts)
        );
        """
    )
    conn.commit()


def store_alerts(conn: sqlite3.Connection, triggered: bool, phi_cps: float, threshold: float, payload: dict, ts: int):
    conn.execute(
        "INSERT OR REPLACE INTO alerts (ts, triggered, phi_cps, threshold, payload) VALUES (?, ?, ?, ?, ?)",
        (ts, 1 if triggered else 0, phi_cps, threshold, json.dumps(payload)),
    )


def store_phi_cps(conn: sqlite3.Connection, value: float, ts: int):
    conn.execute(
        "INSERT OR REPLACE INTO phi_cps (ts, value, components) VALUES (?, ?, ?)",
        (ts, value, json.dumps({"source": "kix"})),
    )


def store_health(conn: sqlite3.Connection, results: list[dict], ts: int):
    for item in results:
        conn.execute(
            "INSERT OR REPLACE INTO health (ts, runner, status, latency_ms, ternary_role, version) VALUES (?, ?, ?, ?, ?, ?)",
            (
                ts,
                item.get("name"),
                item.get("status", "unknown"),
                int(item.get("latency_ms", 0)),
                None,
                item.get("service"),
            ),
        )


def run(kix_url: str, mimir_db: Path, interval: int):
    conn = sqlite3.connect(mimir_db)
    ensure_schema(conn)
    print(f"[bridge] KIX={kix_url} MIMIR={mimir_db} interval={interval}s")
    while True:
        try:
            audit = fetch_kix_audit(kix_url)
            alerts = fetch_kix_alerts(kix_url)
            ts = utcnow_ts()
            store_phi_cps(conn, float(audit.get("phi_cps", 0.0)), ts)
            store_health(conn, audit.get("results", []), ts)
            store_alerts(
                conn,
                bool(alerts.get("triggered")),
                float(alerts.get("phi_cps", 0.0)),
                float(alerts.get("threshold", 0.9)),
                alerts,
                ts,
            )
            conn.commit()
            print(f"[bridge] stored phi_cps={audit.get('phi_cps')} healthy={audit.get('healthy')} total={audit.get('total')} triggered={alerts.get('triggered')}")
        except Exception as exc:
            print(f"[bridge] error: {exc}")
        time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description="KIX → MIMIR bridge")
    parser.add_argument("--kix", default="http://localhost:8800")
    parser.add_argument("--mimir", default=str(Path(__file__).resolve().parents[2] / ".mimir" / "data" / "metrics.db"))
    parser.add_argument("--interval", type=int, default=5)
    args = parser.parse_args()
    run(args.kix, Path(args.mimir), args.interval)


if __name__ == "__main__":
    main()
