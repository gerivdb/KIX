"""Validation E2E du bootstrap runner sur ENV2.

Usage:
    python tests/validate_bootstrap_env2.py

Ce script necessite que KIX ne soit pas deja en cours d'execution.
Il demarre KIX, attend que bootstrap soit pret, puis valide les endpoints.
"""

import os
import sys
import time
import json
import subprocess
import requests
from pathlib import Path

KIX_DIR = Path(__file__).resolve().parent.parent
KIX_APP = KIX_DIR / "src" / "app.py"
BOOTSTRAP_URL = "http://127.0.0.1:8810"
KIX_URL = "http://127.0.0.1:8800"
KIX_DB = KIX_DIR / "data" / "kix_e2e_validation.sqlite"


def main() -> int:
    if not KIX_APP.exists():
        print(f"[ERREUR] KIX introuvable: {KIX_APP}")
        return 1

    env = os.environ.copy()
    env["KIX_PORT"] = "8800"
    env["KIX_DB"] = str(KIX_DB)

    print("[VALIDATION] Demarrage de KIX...")
    kix_process = subprocess.Popen(
        [sys.executable, str(KIX_APP)],
        cwd=str(KIX_DIR),
        env=env,
        creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        # Attendre KIX
        print("[VALIDATION] Attente de KIX (port 8800)...")
        for i in range(60):
            try:
                resp = requests.get(f"{KIX_URL}/health", timeout=1)
                if resp.status_code == 200:
                    print(f"[VALIDATION] KIX pret (tentative {i+1})")
                    break
            except requests.RequestException:
                pass
            time.sleep(1)
        else:
            print("[ERREUR] KIX n'est pas devenu pret dans le delai imparti")
            return 1

        # Attendre bootstrap
        print("[VALIDATION] Attente de bootstrap (port 8810)...")
        bootstrap_ready = False
        for i in range(60):
            try:
                resp = requests.get(f"{BOOTSTRAP_URL}/bootstrap/ready", timeout=1)
                if resp.status_code == 200 and resp.json().get("ready"):
                    print(f"[VALIDATION] Bootstrap pret (tentative {i+1})")
                    bootstrap_ready = True
                    break
            except requests.RequestException:
                pass
            time.sleep(1)

        if not bootstrap_ready:
            print("[ERREUR] Bootstrap n'est pas devenu pret dans le delai imparti")
            return 1

        # Valider endpoints
        print("\n[VALIDATION] Verification des endpoints...")

        endpoints = [
            ("KIX /health", f"{KIX_URL}/health", 200),
            ("bootstrap /health", f"{BOOTSTRAP_URL}/health", 200),
            ("bootstrap /bootstrap/status", f"{BOOTSTRAP_URL}/bootstrap/status", 200),
            ("bootstrap /bootstrap/ready", f"{BOOTSTRAP_URL}/bootstrap/ready", 200),
            ("KIX /runners", f"{KIX_URL}/runners", 200),
        ]

        all_ok = True
        for name, url, expected in endpoints:
            try:
                resp = requests.get(url, timeout=5)
                if resp.status_code == expected:
                    print(f"  [OK] {name} -> {resp.status_code}")
                else:
                    print(f"  [KO] {name} -> {resp.status_code} (attendu {expected})")
                    all_ok = False
            except Exception as exc:
                print(f"  [KO] {name} -> exception: {exc}")
                all_ok = False

        # Verifier que bootstrap est dans /runners
        try:
            resp = requests.get(f"{KIX_URL}/runners", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                runners = {r["name"]: r for r in data.get("runners", [])}
                if "bootstrap" in runners:
                    print("  [OK] bootstrap present dans /runners")
                else:
                    print("  [KO] bootstrap absent de /runners")
                    all_ok = False
        except Exception as exc:
            print(f"  [KO] /runners -> exception: {exc}")
            all_ok = False

        print("\n[VALIDATION] Resultat:", "OK" if all_ok else "KO")
        return 0 if all_ok else 1

    finally:
        print("\n[VALIDATION] Arret de KIX...")
        try:
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(kix_process.pid)], check=False)
            else:
                kix_process.terminate()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())
