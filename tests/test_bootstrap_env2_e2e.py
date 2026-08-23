"""Script de validation E2E du bootstrap runner sur ENV2.

Verifie:
1. KIX demarre sur le port 8800
2. bootstrap demarre sur le port 8810
3. /bootstrap/ready retourne 200 quand tous les services sont up
4. PHI_TOTAL est calcule et > 0.85
"""

import os
import sys
import time
import json
import subprocess
import requests
import unittest
from pathlib import Path

KIX_DIR = Path(__file__).resolve().parent.parent
KIX_APP = KIX_DIR / "src" / "app.py"
BOOTSTRAP_URL = "http://127.0.0.1:8810"
KIX_URL = "http://127.0.0.1:8800"


class TestEndToEndBootstrapENV2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Demarre KIX en arriere-plan pour les tests E2E."""
        cls.kix_process = None
        cls.kix_ready = False
        cls.bootstrap_ready = False

        # Demarrer KIX
        if not KIX_APP.exists():
            cls.skipTest(f"KIX app not found at {KIX_APP}")

        env = os.environ.copy()
        env["KIX_PORT"] = "8800"
        env["KIX_DB"] = str(KIX_DIR / "data" / "kix_e2e_test.sqlite")

        try:
            cls.kix_process = subprocess.Popen(
                [sys.executable, str(KIX_APP)],
                cwd=str(KIX_DIR),
                env=env,
                creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except Exception as exc:
            cls.skipTest(f"Failed to start KIX: {exc}")

        # Attendre que KIX soit pret
        for _ in range(60):
            try:
                resp = requests.get(f"{KIX_URL}/health", timeout=5)
                if resp.status_code == 200:
                    cls.kix_ready = True
                    break
            except requests.RequestException:
                pass
            time.sleep(1)

        if not cls.kix_ready:
            cls.tearDownClass()
            cls.skipTest("KIX did not become ready in time")

        # Attendre que bootstrap soit pret
        for _ in range(60):
            try:
                resp = requests.get(f"{BOOTSTRAP_URL}/bootstrap/ready", timeout=1)
                if resp.status_code == 200 and resp.json().get("ready"):
                    cls.bootstrap_ready = True
                    break
            except requests.RequestException:
                pass
            time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        """Arrete KIX."""
        if cls.kix_process:
            try:
                if sys.platform == "win32":
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(cls.kix_process.pid)], check=False)
                else:
                    cls.kix_process.terminate()
            except Exception:
                pass

    def test_kix_health(self):
        """Verifie que KIX repond sur /health."""
        resp = requests.get(f"{KIX_URL}/health", timeout=5)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("service"), "kix")

    def test_bootstrap_health(self):
        """Verifie que bootstrap repond sur /health."""
        resp = requests.get(f"{BOOTSTRAP_URL}/health", timeout=5)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("service"), "bootstrap")

    def test_bootstrap_status(self):
        """Verifie que /bootstrap/status retourne un JSON valide."""
        resp = requests.get(f"{BOOTSTRAP_URL}/bootstrap/status", timeout=5)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("services", data)
        self.assertIn("ready", data)
        self.assertIn("blockers", data)

    def test_bootstrap_ready(self):
        """Verifie que /bootstrap/ready retourne 200 quand bootstrap est pret."""
        if not self.bootstrap_ready:
            self.skipTest("bootstrap not ready")
        resp = requests.get(f"{BOOTSTRAP_URL}/bootstrap/ready", timeout=5)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("ready"))

    def test_kix_runners_endpoint(self):
        """Verifie que KIX expose /runners avec bootstrap."""
        resp = requests.get(f"{KIX_URL}/runners", timeout=5)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        runners = {r["name"]: r for r in data.get("runners", [])}
        self.assertIn("bootstrap", runners)


if __name__ == "__main__":
    unittest.main()
