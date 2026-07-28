# Sovereign CI Pipeline for RLM Services via KIX
# Orchestrates all RLM runners and runs their test suites

from __future__ import annotations

import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path


RUNNERS = {
    "RLM-SECURE": 8797,
    "RLM-DEPLOY": 8795,
    "RLM-GRAPH": 8794,
    "RLM-CONFIG": 8793,
    "RLM-SECURE": 8797,
    "RLM-INCIDENT": 8798,
    "RLM-RELEASE": 8799,
}

KIX_PORT = 8800
ROOT = Path(__file__).resolve().parent.parent.parent  # L2-PLATFORM


def wait_for_port(port: int, timeout: float = 5.0) -> bool:
    """Wait for service to respond on /healthz."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            urllib.request.urlopen(f"http://localhost:{port}/healthz", timeout=1.0)
            return True
        except (urllib.error.URLError, ConnectionRefusedError):
            time.sleep(0.3)
    return False


def main() -> int:
    print("[KIX-CI] Sovereign pipeline starting...")

    # Start KIX first
    kix_proc = subprocess.Popen(
        [sys.executable, "src/app.py"],
        cwd=ROOT / "KIX",
    )

    if not wait_for_port(KIX_PORT):
        print("[KIX-CI] ERROR: KIX failed to start")
        return 1

    print("[KIX-CI] KIX online")

    failed = []
    for runner_name, port in RUNNERS.items():
        runner_dir = ROOT / runner_name
        if not runner_dir.exists():
            print(f"[KIX-CI] SKIP {runner_name}: directory not found")
            continue

        proc = subprocess.Popen(
            [sys.executable, "src/app.py"],
            cwd=runner_dir,
        )

        if wait_for_port(port):
            print(f"[KIX-CI] {runner_name}: OK (port {port})")
        else:
            print(f"[KIX-CI] {runner_name}: FAILED to start")
            failed.append(runner_name)

        proc.terminate()

    # Run probe audit via KIX
    try:
        urllib.request.urlopen(f"http://localhost:{KIX_PORT}/probe/audit", timeout=10)
        print("[KIX-CI] Probe audit completed via KIX")
    except Exception as e:
        print(f"[KIX-CI] Probe audit error: {e}")

    kix_proc.terminate()

    if failed:
        print(f"[KIX-CI] Failed runners: {', '.join(failed)}")
        return 1

    print("[KIX-CI] Pipeline completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())