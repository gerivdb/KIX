"""Validation runtime rapide des endpoints KIX Generic Runner Wrapper."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Script is under .kilo/worktrees/snow-moose/scripts/, repo root is 3 levels up
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault("KIX_DB", str(REPO_ROOT / "data" / "kix-runtime-test.sqlite"))
os.environ.setdefault("KIX_NOTIFICATIONS_DB", str(REPO_ROOT / "data" / "notifications-runtime-test.db"))
os.environ.setdefault("KIX_AUDIT_DB", str(REPO_ROOT / "data" / "audit-runtime-test.db"))

from src.app import app

app.config["TESTING"] = True
client = app.test_client()


def check(name: str, path: str) -> None:
    resp = client.get(path)
    data = resp.get_json()
    print(f"[OK] {name}: {path} -> {resp.status_code}")
    if name == "swarm":
        runners = list(data.get("runners", {}).keys())
        print(f"       runners={runners}")
    elif name == "doctor":
        print(f"       total={data.get('total')} unhealthy={data.get('unhealthy')}")


check("swarm", "/swarm/status")
check("doctor", "/doctor")
print("[VALIDATION] runtime endpoints OK")
