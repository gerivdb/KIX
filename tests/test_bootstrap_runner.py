"""Tests unitaires pour bootstrap_runner."""

import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock
from io import BytesIO

# Ajout du chemin pour importer le module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "services"))

import bootstrap_runner as bootstrap


class TestCheckPort(unittest.TestCase):
    def test_open_port(self):
        with patch("socket.create_connection") as mock_conn:
            mock_conn.return_value = MagicMock()
            self.assertTrue(bootstrap.check_port("127.0.0.1", 8810, timeout=0.1))

    def test_closed_port(self):
        with patch("socket.create_connection", side_effect=OSError):
            self.assertFalse(bootstrap.check_port("127.0.0.1", 8810, timeout=0.1))


class TestCheckService(unittest.TestCase):
    def setUp(self):
        bootstrap.state = bootstrap.BootstrapState()

    def test_running_service(self):
        with patch.object(bootstrap, "check_port", return_value=True):
            result = bootstrap.check_service("test-service", {"port": 8080, "path": "/health", "required": True})
            self.assertEqual(result["status"], "running")

    def test_stopped_required_service(self):
        with patch.object(bootstrap, "check_port", return_value=False):
            result = bootstrap.check_service("test-service", {"port": 8080, "path": "/health", "required": True})
            self.assertEqual(result["status"], "stopped")
            self.assertIn("test-service: port 8080 not reachable", bootstrap.state.blockers)

    def test_stopped_optional_service(self):
        with patch.object(bootstrap, "check_port", return_value=False):
            result = bootstrap.check_service("flex-api", {"port": 8080, "path": "/health", "required": False})
            self.assertEqual(result["status"], "stopped")
            self.assertNotIn("flex-api", bootstrap.state.blockers)


class TestResolveSecret(unittest.TestCase):
    def setUp(self):
        bootstrap.state = bootstrap.BootstrapState()

    def test_resolve_from_env(self):
        with patch.dict(os.environ, {"MY_SECRET": "env_value"}):
            self.assertEqual(bootstrap.resolve_secret("MY_SECRET"), "env_value")

    def test_resolve_from_keyring(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch("keyring.get_password", return_value="keyring_value"):
                self.assertEqual(bootstrap.resolve_secret("MY_SECRET"), "keyring_value")

    def test_resolve_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch("keyring.get_password", return_value=None):
                self.assertIsNone(bootstrap.resolve_secret("MISSING_SECRET"))


class TestBootstrapState(unittest.TestCase):
    def setUp(self):
        bootstrap.state = bootstrap.BootstrapState()

    def test_initial_state(self):
        self.assertEqual(bootstrap.state.status, bootstrap.PHASE_PENDING)
        self.assertEqual(bootstrap.state.phase, bootstrap.PHASE_PENDING)
        self.assertFalse(bootstrap.state.ready)
        self.assertEqual(bootstrap.state.blockers, [])

    def test_to_dict(self):
        d = bootstrap.state.to_dict()
        self.assertIn("status", d)
        self.assertIn("phase", d)
        self.assertIn("timestamp", d)
        self.assertIn("services", d)
        self.assertIn("ready", d)
        self.assertIn("blockers", d)


class TestBootstrapHandler(unittest.TestCase):
    def setUp(self):
        bootstrap.state = bootstrap.BootstrapState()

    def _make_request(self, method, path):
        handler = bootstrap.BootstrapHandler.__new__(bootstrap.BootstrapHandler)
        handler.requestline = f"{method} {path} HTTP/1.1"
        handler.request_version = "HTTP/1.1"
        handler.command = method
        handler.path = path
        handler.headers = {}
        handler.wfile = BytesIO()
        handler.rfile = BytesIO()
        handler.client_address = ("127.0.0.1", 12345)
        handler.server = MagicMock()
        handler.close_connection = False
        return handler

    def test_health_get(self):
        handler = self._make_request("GET", "/health")
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()
        handler.do_GET()
        handler.send_response.assert_called_with(200)

    def test_status_get(self):
        handler = self._make_request("GET", "/bootstrap/status")
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()
        handler.do_GET()
        handler.send_response.assert_called_with(200)

    def test_ready_get_not_ready(self):
        bootstrap.state.ready = False
        handler = self._make_request("GET", "/bootstrap/ready")
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()
        handler.do_GET()
        handler.send_response.assert_called_with(503)

    def test_start_post(self):
        handler = self._make_request("POST", "/bootstrap/start")
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()
        bootstrap.state.phase = bootstrap.PHASE_PENDING
        handler.do_POST()
        handler.send_response.assert_called_with(202)

    def test_monitor_get_ok(self):
        bootstrap.state.ready = True
        bootstrap.state.blockers = []
        handler = self._make_request("GET", "/bootstrap/monitor")
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()
        handler.do_GET()
        handler.send_response.assert_called_with(200)

    def test_monitor_get_alert(self):
        bootstrap.state.ready = False
        bootstrap.state.blockers = ["test: port 1234 not reachable"]
        handler = self._make_request("GET", "/bootstrap/monitor")
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()
        handler.do_GET()
        handler.send_response.assert_called_with(503)


class TestBootstrapMonitor(unittest.TestCase):
    def setUp(self):
        bootstrap.state = bootstrap.BootstrapState()
        bootstrap.monitor = bootstrap.BootstrapMonitor()

    def test_monitor_ok(self):
        bootstrap.state.ready = True
        report = bootstrap.monitor.check()
        self.assertIsNone(report.get("alert"))
        self.assertEqual(report["alert_count"], 0)

    def test_monitor_alert_on_blockers(self):
        bootstrap.state.blockers = ["service: port 1234 not reachable"]
        report = bootstrap.monitor.check()
        self.assertIsNotNone(report.get("alert"))
        self.assertEqual(report["alert_count"], 1)

    def test_monitor_alert_on_not_ready(self):
        bootstrap.state.ready = False
        bootstrap.state.phase = bootstrap.PHASE_CHECKING
        report = bootstrap.monitor.check()
        self.assertIsNotNone(report.get("alert"))
        self.assertIn("not ready", report["alert"])


if __name__ == "__main__":
    unittest.main()
