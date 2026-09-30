"""Tests for kix/libs/shared-clients/kg_l_client.py remote mode."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure kix package is importable
_KIX_ROOT = Path(__file__).resolve().parents[2]
if str(_KIX_ROOT) not in sys.path:
    sys.path.insert(0, str(_KIX_ROOT))

# Mock kg_l module before importing KG_L_Client
# because kg_l is not installed as a package in test environment
_mock_kg_l = MagicMock()
_mock_kg_l.KGLEngine = MagicMock
sys.modules["kg_l"] = _mock_kg_l

from kix.libs.shared_clients.kg_l_client import KG_L_Client  # noqa: E402


def _make_resp(payload: dict) -> MagicMock:
    mock_resp = MagicMock()
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_resp.read.return_value = json.dumps(payload).encode("utf-8")
    return mock_resp


class TestKGLClientRemote:
    def test_remote_query(self):
        client = KG_L_Client(host="http://localhost:8888")
        with patch("urllib.request.urlopen", return_value=_make_resp({"results": [{"name": "node1"}]})):
            result = client.query("MATCH (n) RETURN n LIMIT 1")
        assert result == [{"name": "node1"}]

    def test_remote_get_hubs(self):
        client = KG_L_Client(host="http://localhost:8888")
        with patch("urllib.request.urlopen", return_value=_make_resp({"hubs": [{"name": "hub1", "degree": 10}]})):
            result = client.get_hubs(limit=10, min_degree=5)
        assert result == [{"name": "hub1", "degree": 10}]

    def test_remote_get_graph_stats(self):
        client = KG_L_Client(host="http://localhost:8888")
        with patch("urllib.request.urlopen", return_value=_make_resp({"nodes": 100, "edges": 200, "components": 1, "chi": 2})):
            result = client.get_graph_stats()
        assert result == {"nodes": 100, "edges": 200, "components": 1, "chi": 2}

    def test_remote_ingest(self):
        client = KG_L_Client(host="http://localhost:8888")
        with patch("urllib.request.urlopen", return_value=_make_resp({"status": "ok", "ingested": 5})):
            result = client.ingest([{"id": "1"}], [{"src": "1", "dst": "2"}])
        assert result == {"status": "ok", "ingested": 5}

    def test_remote_health(self):
        client = KG_L_Client(host="http://localhost:8888")
        with patch("urllib.request.urlopen", return_value=_make_resp({"status": "ok"})):
            result = client.health()
        assert result == {"status": "ok"}

    def test_remote_health_failure(self):
        client = KG_L_Client(host="http://localhost:8888")
        with patch("urllib.request.urlopen", side_effect=Exception("unreachable")):
            result = client.health()
        assert result["status"] == "unreachable"
