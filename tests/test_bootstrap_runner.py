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


class TestDependencies(unittest.TestCase):
    """G1 (PRD-MOC-GEN-002) : le bus WAZAA réel écoute sur 1873."""

    def test_wazaa_bus_port_is_1873(self):
        self.assertEqual(bootstrap.DEPENDENCIES["wazaa"]["port"], 1873)
        self.assertTrue(bootstrap.DEPENDENCIES["wazaa"]["required"])

    def test_wazaa_mission_control_optional_5002(self):
        mc = bootstrap.DEPENDENCIES["wazaa-mc"]
        self.assertEqual(mc["port"], 5002)
        self.assertFalse(mc["required"])

    def test_wazaa_threads_informational_8200(self):
        threads = bootstrap.DEPENDENCIES["wazaa-threads"]
        self.assertEqual(threads["port"], 8200)
        self.assertFalse(threads["required"])


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


class TestCheckAllDependencies(unittest.TestCase):
    """Sémantique ready auto-guérie (PRD-MOC-GEN-002 §7.4)."""

    def setUp(self):
        bootstrap.state = bootstrap.BootstrapState()

    def test_all_up_sets_ready(self):
        with patch.object(bootstrap, "check_port", return_value=True):
            self.assertTrue(bootstrap.check_all_dependencies())
            self.assertTrue(bootstrap.state.ready)
            self.assertEqual(bootstrap.state.status, bootstrap.PHASE_READY)
            self.assertEqual(bootstrap.state.phase, "operational")

    def test_required_down_blocks_ready(self):
        with patch.object(bootstrap, "check_port", return_value=False):
            self.assertFalse(bootstrap.check_all_dependencies())
            self.assertFalse(bootstrap.state.ready)
            self.assertGreater(len(bootstrap.state.blockers), 0)
            self.assertNotEqual(bootstrap.state.status, bootstrap.PHASE_READY)


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
        # Déterminisme : tous les ports fermés -> ready=False -> 503
        with patch.object(bootstrap, "check_port", return_value=False):
            handler = self._make_request("GET", "/bootstrap/ready")
            handler.send_response = MagicMock()
            handler.send_header = MagicMock()
            handler.end_headers = MagicMock()
            handler.do_GET()
            handler.send_response.assert_called_with(503)

    def test_ready_get_all_up(self):
        with patch.object(bootstrap, "check_port", return_value=True):
            handler = self._make_request("GET", "/bootstrap/ready")
            handler.send_response = MagicMock()
            handler.send_header = MagicMock()
            handler.end_headers = MagicMock()
            handler.do_GET()
            handler.send_response.assert_called_with(200)

    def test_start_post(self):
        # Le starter réel est mocké : pas de démarrage de services pendant les tests
        with patch.object(bootstrap, "ServiceStarter") as mock_starter:
            handler = self._make_request("POST", "/bootstrap/start")
            handler.send_response = MagicMock()
            handler.send_header = MagicMock()
            handler.end_headers = MagicMock()
            bootstrap.state.phase = bootstrap.PHASE_PENDING
            handler.do_POST()
            handler.send_response.assert_called_with(202)
            mock_starter.assert_called_once()

    def _post_json(self, path, payload):
        import json as _json

        handler = self._make_request("POST", path)
        body = _json.dumps(payload).encode("utf-8")
        handler.headers = {"Content-Type": "application/json", "Content-Length": str(len(body))}
        handler.rfile = BytesIO(body)
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()
        return handler

    def test_register_post_ok(self):
        handler = self._post_json("/bootstrap/register", {"name": "svc-x", "port": 9999})
        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {"status": "registered"}
            handler.do_POST()
        handler.send_response.assert_called_with(200)

    def test_register_post_missing_fields(self):
        handler = self._post_json("/bootstrap/register", {"name": "svc-x"})
        handler.do_POST()
        handler.send_response.assert_called_with(400)

    def test_register_post_invalid_json(self):
        handler = self._make_request("POST", "/bootstrap/register")
        body = b"not-json"
        handler.headers = {"Content-Length": str(len(body))}
        handler.rfile = BytesIO(body)
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()
        handler.do_POST()
        handler.send_response.assert_called_with(400)

    def test_monitor_get_ok(self):
        with patch.object(bootstrap, "check_port", return_value=True):
            handler = self._make_request("GET", "/bootstrap/monitor")
            handler.send_response = MagicMock()
            handler.send_header = MagicMock()
            handler.end_headers = MagicMock()
            handler.do_GET()
            handler.send_response.assert_called_with(200)

    def test_monitor_get_alert(self):
        with patch.object(bootstrap, "check_port", return_value=False):
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

    def test_single_class_definition(self):
        """Régression : BootstrapMonitor ne doit être défini qu'une seule fois."""
        import inspect

        source = inspect.getsource(bootstrap)
        self.assertEqual(source.count("class BootstrapMonitor"), 1)

    def test_monitor_ok(self):
        with patch.object(bootstrap, "check_port", return_value=True):
            report = bootstrap.monitor.check()
            self.assertIsNone(report.get("alert"))
            self.assertEqual(report["alert_count"], 0)

    def test_monitor_alert_on_blockers(self):
        with patch.object(bootstrap, "check_port", return_value=False):
            report = bootstrap.monitor.check()
            self.assertIsNotNone(report.get("alert"))
            self.assertGreaterEqual(report["alert_count"], 1)

    def test_monitor_alert_on_not_ready(self):
        with patch.object(bootstrap, "check_port", side_effect=lambda host, port, timeout=1.0: port == 8810):
            # Seul 8810 répond : les dépendances requises sont down -> not ready
            bootstrap.monitor.check()
            bootstrap.state.ready = False
            bootstrap.state.phase = bootstrap.PHASE_CHECKING
            report = bootstrap.monitor.check()
            self.assertIsNotNone(report.get("alert"))


class TestBootstrapWatchdog(unittest.TestCase):
    """Auto-cicatrisation PRD-MOC-GEN-002 §11 (dispo >99%, recovery <10s)."""

    def setUp(self):
        bootstrap.state = bootstrap.BootstrapState()

    def test_tick_no_action_when_all_up(self):
        wd = bootstrap.BootstrapWatchdog(interval=10)
        with patch.object(bootstrap, "check_port", return_value=True):
            report = wd.tick()
        self.assertEqual(report["action"], "none")
        self.assertTrue(report["ready"])
        self.assertEqual(wd.restarts, 0)

    def test_tick_restarts_when_required_down(self):
        wd = bootstrap.BootstrapWatchdog(interval=10)
        with patch.object(bootstrap, "check_port", return_value=False), \
             patch.object(bootstrap, "ServiceStarter") as mock_starter:
            report = wd.tick()
        self.assertEqual(report["action"], "restarted")
        self.assertEqual(wd.restarts, 1)
        mock_starter.assert_called_once()

    def test_tick_skips_while_starting(self):
        wd = bootstrap.BootstrapWatchdog(interval=10)
        bootstrap.state.rebooting = True  # sequence deja en cours
        with patch.object(bootstrap, "check_port", return_value=False), \
             patch.object(bootstrap, "ServiceStarter") as mock_starter:
            report = wd.tick()
        self.assertEqual(report["action"], "in_progress")
        mock_starter.assert_not_called()


class TestPreflightSingletonGuard(unittest.TestCase):
    """ERR-001 (session 2026-08-23) : double-bind SO_REUSEADDR sous Windows."""

    def test_refuses_when_bootstrap_already_answers(self):
        import urllib.error

        payload = json.dumps({"status": "ok", "service": "bootstrap", "build": "ZOMBIE"}).encode("utf-8")
        mock_resp = MagicMock()
        mock_resp.__enter__.return_value.read.return_value = payload
        with patch("urllib.request.urlopen", return_value=mock_resp), \
             patch.object(bootstrap.logger, "error") as mock_log:
            with self.assertRaises(SystemExit) as ctx:
                bootstrap.preflight_singleton_guard()
            self.assertEqual(ctx.exception.code, 2)
            self.assertIn("DEJA ACTIVE", mock_log.call_args.args[1])

    def test_allows_when_nothing_answers(self):
        import urllib.error

        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("conn refused")):
            # Ne doit pas lever
            bootstrap.preflight_singleton_guard()

    def test_allows_when_foreign_service_answers(self):
        payload = json.dumps({"status": "ok", "service": "autre-chose"}).encode("utf-8")
        mock_resp = MagicMock()
        mock_resp.__enter__.return_value.read.return_value = payload
        with patch("urllib.request.urlopen", return_value=mock_resp):
            bootstrap.preflight_singleton_guard()

    def test_health_exposes_build_id(self):
        bootstrap.state = bootstrap.BootstrapState()
        handler = bootstrap.BootstrapHandler.__new__(bootstrap.BootstrapHandler)
        handler.requestline = "GET /health HTTP/1.1"
        handler.request_version = "HTTP/1.1"
        handler.command = "GET"
        handler.path = "/health"
        handler.headers = {}
        handler.wfile = BytesIO()
        handler.rfile = BytesIO()
        handler.client_address = ("127.0.0.1", 12345)
        handler.server = MagicMock()
        handler.close_connection = False
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()
        handler.do_GET()
        # send_response/send_header sont mockés : wfile ne contient que le corps JSON
        body = json.loads(handler.wfile.getvalue())
        self.assertEqual(body["service"], "bootstrap")
        self.assertIn("build", body)


class TestParallelProbeLatency(unittest.TestCase):
    """ERR-002 : le coût d'un check complet doit rester borné même si les
    sondes individuelles sont lentes (parallélisation ThreadPoolExecutor)."""

    def setUp(self):
        bootstrap.state = bootstrap.BootstrapState()

    def test_parallel_check_completes_quickly_with_slow_probes(self):
        import time as _time

        def slow_probe(host, port, timeout=1.0):
            _time.sleep(0.3)
            return True

        t0 = _time.time()
        with patch.object(bootstrap, "check_port", side_effect=slow_probe):
            ok = bootstrap.check_all_dependencies()
        elapsed = _time.time() - t0
        self.assertTrue(ok)
        # 8 sondes x 0.3s séquentielles = 2.4s ; parallélisé ~0.4s max
        self.assertLess(elapsed, 1.5, f"check trop lent: {elapsed:.2f}s (probablement sequentiel)")


if __name__ == "__main__":
    unittest.main()
