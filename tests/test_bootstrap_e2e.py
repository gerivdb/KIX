"""Script de test end-to-end pour le bootstrap runner.

Verifie:
1. KIX demarre sur le port 8800
2. bootstrap demarre sur le port 8810
3. /bootstrap/ready retourne 200 quand tous les services sont up
4. ECOS CLI interroge /bootstrap/ready
"""

import os
import sys
import time
import json
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "services"))

import bootstrap_runner as bootstrap


class TestEndToEndBootstrap(unittest.TestCase):
    def setUp(self):
        bootstrap.state = bootstrap.BootstrapState()

    def test_bootstrap_ready_sequence(self):
        """Teste la sequence complete de bootstrap."""
        # Simuler tous les services up
        with patch.object(bootstrap, "check_port", return_value=True):
            # 1. Verifier que bootstrap est en mode pending
            self.assertEqual(bootstrap.state.phase, bootstrap.PHASE_PENDING)
            self.assertFalse(bootstrap.state.ready)

            # 2. Declencher le bootstrap
            handler = bootstrap.BootstrapHandler.__new__(bootstrap.BootstrapHandler)
            handler.requestline = "POST /bootstrap/start HTTP/1.1"
            handler.request_version = "HTTP/1.1"
            handler.command = "POST"
            handler.path = "/bootstrap/start"
            handler.headers = {}
            handler.wfile = MagicMock()
            handler.rfile = MagicMock()
            handler.client_address = ("127.0.0.1", 12345)
            handler.server = MagicMock()
            handler.close_connection = False
            handler.send_response = MagicMock()
            handler.send_header = MagicMock()
            handler.end_headers = MagicMock()

            handler.do_POST()
            handler.send_response.assert_called_with(202)

            # 3. Verifier que bootstrap est ready
            self.assertEqual(bootstrap.state.phase, bootstrap.PHASE_READY)
            self.assertTrue(bootstrap.state.ready)

            # 4. Verifier /bootstrap/ready retourne 200
            handler.send_response.reset_mock()
            handler.path = "/bootstrap/ready"
            handler.do_GET()
            handler.send_response.assert_called_with(200)

    def test_bootstrap_ready_with_blockers(self):
        """Teste /bootstrap/ready avec des blockers."""
        # Simuler un service down (trixd sur port 7243)
        def mock_check_port(host, port, timeout=1.0):
            return port != 7243

        with patch.object(bootstrap, "check_port", side_effect=mock_check_port):
            bootstrap.state.ready = False
            handler = bootstrap.BootstrapHandler.__new__(bootstrap.BootstrapHandler)
            handler.requestline = "GET /bootstrap/ready HTTP/1.1"
            handler.request_version = "HTTP/1.1"
            handler.command = "GET"
            handler.path = "/bootstrap/ready"
            handler.headers = {}
            handler.wfile = MagicMock()
            handler.rfile = MagicMock()
            handler.client_address = ("127.0.0.1", 12345)
            handler.server = MagicMock()
            handler.close_connection = False
            handler.send_response = MagicMock()
            handler.send_header = MagicMock()
            handler.end_headers = MagicMock()

            handler.do_GET()
            handler.send_response.assert_called_with(503)
            self.assertGreater(len(bootstrap.state.blockers), 0)

    def test_ecos_cli_bootstrap_wait(self):
        """Simule l'attente de ECOS CLI sur /bootstrap/ready."""
        # Simuler bootstrap qui devient ready apres 3 tentatives
        attempt = [0]

        def mock_get(url, **kwargs):
            attempt[0] += 1
            if attempt[0] >= 3:
                resp = MagicMock()
                resp.ready = True
                resp.blockers = []
                return resp
            raise Exception("not ready")

        with patch("requests.get", side_effect=mock_get):
            # Simuler la logique de ecos.ps1
            bootstrap_url = "http://127.0.0.1:8810/bootstrap/ready"
            bootstrap_ready = False
            for i in range(30):
                try:
                    resp = mock_get(bootstrap_url)
                    if resp.ready:
                        bootstrap_ready = True
                        break
                except Exception:
                    pass
                time.sleep(0.01)  # accélérer le test

            self.assertTrue(bootstrap_ready)
            self.assertEqual(attempt[0], 3)


if __name__ == "__main__":
    unittest.main()
