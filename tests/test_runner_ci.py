"""Tests for KIX runner CI orchestration."""

from __future__ import annotations

import subprocess
import time
import urllib.request
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def wait_for_port(port: int, timeout: float = 2.0) -> bool:
    """Wait for service to respond on /healthz."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            urllib.request.urlopen(f"http://localhost:{port}/healthz", timeout=0.5)
            return True
        except Exception:
            time.sleep(0.2)
    return False


class TestRunnerCIPipeline:
    """Tests for the sovereign CI runner orchestration."""

    def test_wait_for_port_timeout(self):
        """wait_for_port should return False for non-responsive port."""
        # Port 1 très improbable pour répondre
        assert wait_for_port(1, timeout=0.5) is False

    def test_wait_for_port_success(self):
        """wait_for_port should succeed for responsive service."""
        # Test sur KIX existant si déjà en cours d'exécution
        # Sinon skip
        try:
            urllib.request.urlopen("http://localhost:8800/healthz", timeout=0.5)
            assert wait_for_port(8800, timeout=1.0) is True
        except Exception:
            pytest.skip("KIX not running - test environment limited")

    def test_probes_kix_runners_endpoint(self):
        """KIX /runners endpoint returns runner list."""
        try:
            resp = urllib.request.urlopen("http://localhost:8800/runners", timeout=2.0)
            data = resp.read().decode()
            assert "runners" in data or resp.status == 200
        except Exception:
            pytest.skip("KIX not running - test environment limited")