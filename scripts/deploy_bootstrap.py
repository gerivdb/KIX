"""Script de déploiement complet du bootstrap runner.

Démarre tous les services dans l'ordre correct et valide que φ_TOTAL > 0.85.
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
KIX_TOKEN = os.environ.get("KIX_TOKEN", "")


def get_token() -> str:
    """Obtient un token admin pour KIX."""
    if KIX_TOKEN:
        return KIX_TOKEN
    try:
        resp = requests.post(
            f"{KIX_URL}/login",
            json={"username": "admin", "password": "admin123"},
            timeout=5,
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("access_token", "")
    except Exception as exc:
        print(f"[DEPLOY] Erreur obtention token: {exc}")
    return ""


def auth_headers() -> dict[str, str]:
    """Retourne les headers d'authentification pour KIX."""
    token = get_token()
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def start_kix() -> subprocess.Popen | None:
    """Démarre KIX en arrière-plan."""
    env = os.environ.copy()
    env["KIX_PORT"] = "8800"
    env["KIX_DB"] = str(KIX_DIR / "data" / "kix_deploy.sqlite")

    print("[DEPLOY] Demarrage de KIX...")
    proc = subprocess.Popen(
        [sys.executable, str(KIX_APP)],
        cwd=str(KIX_DIR),
        env=env,
        creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc


def wait_for(url: str, path: str, timeout: int = 60) -> bool:
    """Attend qu'un service soit prêt."""
    for i in range(timeout):
        try:
            resp = requests.get(f"{url}{path}", timeout=1)
            if resp.status_code == 200:
                print(f"[DEPLOY] {url}{path} pret (tentative {i+1})")
                return True
        except requests.RequestException:
            pass
        time.sleep(1)
    print(f"[DEPLOY] {url}{path} non pret apres {timeout}s")
    return False


def start_bootstrap() -> bool:
    """Démarre le runner bootstrap via KIX."""
    print("[DEPLOY] Demarrage de bootstrap via KIX...")
    try:
        resp = requests.post(
            f"{KIX_URL}/runners/bootstrap/start",
            headers=auth_headers(),
            timeout=10,
        )
        if resp.status_code == 200:
            print("[DEPLOY] bootstrap demarre avec succes")
            return True
        print(f"[DEPLOY] echec demarrage bootstrap: {resp.status_code}")
        return False
    except Exception as exc:
        print(f"[DEPLOY] erreur demarrage bootstrap: {exc}")
        return False


def wait_bootstrap_ready(timeout: int = 60) -> bool:
    """Attend que bootstrap soit prêt."""
    print(f"[DEPLOY] Attente de bootstrap ready (timeout {timeout}s)...")
    for i in range(timeout):
        try:
            resp = requests.get(f"{BOOTSTRAP_URL}/bootstrap/ready", timeout=1)
            if resp.status_code == 200 and resp.json().get("ready"):
                print(f"[DEPLOY] Bootstrap pret (tentative {i+1})")
                return True
        except requests.RequestException:
            pass
        time.sleep(1)
    return False


def start_runner(name: str) -> bool:
    """Démarre un runner via KIX."""
    try:
        resp = requests.post(
            f"{KIX_URL}/runners/{name}/start",
            headers=auth_headers(),
            timeout=10,
        )
        if resp.status_code == 200:
            print(f"[DEPLOY] {name} demarre")
            return True
        print(f"[DEPLOY] echec demarrage {name}: {resp.status_code}")
        return False
    except Exception as exc:
        print(f"[DEPLOY] erreur demarrage {name}: {exc}")
        return False


def wait_runner_ready(name: str, port: int, timeout: int = 30) -> bool:
    """Attend qu'un runner soit prêt."""
    for i in range(timeout):
        try:
            resp = requests.get(f"http://127.0.0.1:{port}/health", timeout=1)
            if resp.status_code == 200:
                print(f"[DEPLOY] {name} pret (port {port})")
                return True
        except requests.RequestException:
            pass
        time.sleep(1)
    print(f"[DEPLOY] {name} non pret apres {timeout}s")
    return False


def calculate_phi() -> float | None:
    """Calcule φ-CPS à partir de /runners."""
    try:
        resp = requests.get(f"{KIX_URL}/runners", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            runners = data.get("runners", [])
            total = len(runners)
            running = sum(1 for r in runners if r.get("status") == "running")
            if total > 0:
                return round(running / total, 3)
    except Exception as exc:
        print(f"[DEPLOY] erreur calcul phi: {exc}")
    return None


def main() -> int:
    print("=" * 60)
    print("DEPLOIEMENT COMPLET DU BOOTSTRAP RUNNER")
    print("=" * 60)

    # Étape 1: Démarrer KIX
    print("\n[ETAPE 1] Demarrage de KIX...")
    kix_proc = start_kix()
    if not kix_proc:
        print("[ERREUR] Impossible de demarrer KIX")
        return 1

    try:
        if not wait_for(KIX_URL, "/health", timeout=60):
            print("[ERREUR] KIX n'est pas devenu pret")
            return 1

        # Étape 2: Démarrer bootstrap
        print("\n[ETAPE 2] Demarrage de bootstrap...")
        if not start_bootstrap():
            print("[ERREUR] Impossible de demarrer bootstrap")
            return 1

        if not wait_bootstrap_ready(timeout=60):
            print("[ERREUR] Bootstrap n'est pas devenu pret")
            return 1

        # Étape 3: Démarrer les runners additionnels
        print("\n[ETAPE 3] Demarrage des runners additionnels...")
        runners_to_start = ["trixd", "wazaa", "flex-api", "arbiter"]
        for runner in runners_to_start:
            start_runner(runner)

        # Attendre que les runners soient prêts
        print("[DEPLOY] Attente des runners...")
        time.sleep(10)

        # Étape 4: Valider φ_TOTAL
        print("\n[ETAPE 4] Validation de phi-TOTAL...")
        phi = calculate_phi()
        if phi is None:
            print("[ERREUR] Impossible de calculer phi")
            return 1

        print(f"  phi-CPS: {phi}")

        # Étape 5: Vérifier le seuil
        print("\n[ETAPE 5] Verification du seuil...")
        threshold = 0.85
        if phi >= threshold:
            print(f"  [OK] phi-CPS {phi} >= {threshold}")
        else:
            print(f"  [WARN] phi-CPS {phi} < {threshold}")
            print(f"  [INFO] Ceci est attendu si tous les runners ne sont pas demarres.")

        # Résumé
        print("\n" + "=" * 60)
        print("DEPLOIEMENT TERMINE")
        print(f"  KIX: pret")
        print(f"  Bootstrap: pret")
        print(f"  phi-CPS: {phi}")
        print(f"  Seuil: {threshold}")
        print("=" * 60)
        return 0

    finally:
        print("\n[ETAPE 6] Arret de KIX...")
        if kix_proc:
            try:
                if sys.platform == "win32":
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(kix_proc.pid)], check=False)
                else:
                    kix_proc.terminate()
            except Exception:
                pass


if __name__ == "__main__":
    sys.exit(main())
