"""Tests d'intégration pour bootstrap_runner avec KIX."""

import os
import sys
import json
import time
import socket
import unittest
from unittest.mock import patch, MagicMock
from io import BytesIO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "services"))

import bootstrap_runner as bootstrap


class TestIntegrationServiceStarter(unittest.TestCase):
    def setUp(self):
        bootstrap.state = bootstrap.BootstrapState()

    def test_service_starter_sequence(self):
        starter = bootstrap.ServiceStarter()
        starter.start()
        self.assertEqual(bootstrap.state.phase, bootstrap.PHASE_READY)
        self.assertTrue(bootstrap.state.ready)

    def test_kix_registrar_register(self):
        registrar = bootstrap.KIXRegistrar()
        result = registrar.register_runner("test-runner", 8080)
        # TODO: implémenter l'appel HTTP vers KIX /runners/register
        self.assertFalse(result)


class TestIntegrationBootstrapReady(unittest.TestCase):
    def setUp(self):
        bootstrap.state = bootstrap.BootstrapState()

    def test_ready_requires_all_services(self):
        # Simuler tous les services down
        with patch.object(bootstrap, "check_port", return_value=False):
            handler = bootstrap.BootstrapHandler.__new__(bootstrap.BootstrapHandler)
            handler.requestline = "GET /bootstrap/ready HTTP/1.1"
            handler.request_version = "HTTP/1.1"
            handler.command = "GET"
            handler.path = "/bootstrap/ready"
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
            handler.send_response.assert_called_with(503)

    def test_ready_when_all_services_up(self):
        # Simuler tous les services up + ready
        with patch.object(bootstrap, "check_port", return_value=True):
            bootstrap.state.ready = True
            bootstrap.state.blockers = []
            handler = bootstrap.BootstrapHandler.__new__(bootstrap.BootstrapHandler)
            handler.requestline = "GET /bootstrap/ready HTTP/1.1"
            handler.request_version = "HTTP/1.1"
            handler.command = "GET"
            handler.path = "/bootstrap/ready"
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
            handler.send_response.assert_called_with(200)


if __name__ == "__main__":
    unittest.main()
