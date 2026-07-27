import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts.kix_mimir_bridge import ensure_schema, store_health, store_phi_cps, store_alerts, fetch_kix_audit, fetch_kix_alerts


def test_store_phi_cps(tmp_path: Path):
    db = tmp_path / "metrics.db"
    conn = sqlite3.connect(db)
    ensure_schema(conn)
    store_phi_cps(conn, 4.2, 1000000)
    row = conn.execute("SELECT value FROM phi_cps WHERE ts = 1000000").fetchone()
    assert row is not None
    assert row[0] == 4.2
    conn.close()


def test_store_health(tmp_path: Path):
    db = tmp_path / "metrics.db"
    conn = sqlite3.connect(db)
    ensure_schema(conn)
    store_health(conn, [{"name": "RLM-GRAPH", "status": "ok", "latency_ms": 12.3, "service": "rlm-graph"}], 1000001)
    row = conn.execute("SELECT runner, status FROM health WHERE ts = 1000001").fetchone()
    assert row is not None
    assert row[0] == "RLM-GRAPH"
    assert row[1] == "ok"
    conn.close()


def test_fetch_kix_audit():
    fake = MagicMock()
    fake.status_code = 200
    fake.json.return_value = {"phi_cps": 0.87, "healthy": 11, "total": 13, "results": []}
    with patch("scripts.kix_mimir_bridge.requests.get", return_value=fake):
        data = fetch_kix_audit("http://localhost:8800")
        assert data["phi_cps"] == 0.87


def test_store_alerts(tmp_path: Path):
    db = tmp_path / "metrics.db"
    conn = sqlite3.connect(db)
    ensure_schema(conn)
    store_alerts(conn, True, 0.7, 0.9, {"phi_cps": 0.7, "items": []}, 1000002)
    row = conn.execute("SELECT triggered, phi_cps, threshold FROM alerts WHERE ts = 1000002").fetchone()
    assert row is not None
    assert row[0] == 1
    assert row[1] == 0.7
    assert row[2] == 0.9
    conn.close()


def test_fetch_kix_alerts():
    fake = MagicMock()
    fake.status_code = 200
    fake.json.return_value = {"triggered": True, "phi_cps": 0.7, "threshold": 0.9, "items": []}
    with patch("scripts.kix_mimir_bridge.requests.get", return_value=fake):
        data = fetch_kix_alerts("http://localhost:8800")
        assert data["triggered"] is True
        assert data["phi_cps"] == 0.7
