"""Tests for src/brain_cognitive_client.py."""

from __future__ import annotations

import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from src.brain_cognitive_client import BrainCognitiveClient, BrainCognitiveError


class TestBrainCognitiveClient:
    def test_trigger_agent(self):
        client = BrainCognitiveClient()
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = b'{"result": {"task_id": "123"}}'
            mock_resp.__enter__ = MagicMock(return_value=mock_resp)
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_resp
            result = client.trigger_agent("architect", {"epic": "EPIC-123"})
        assert result["task_id"] == "123"

    def test_get_result(self):
        client = BrainCognitiveClient()
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = b'{"result": {"status": "completed"}}'
            mock_resp.__enter__ = MagicMock(return_value=mock_resp)
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_resp
            result = client.get_result("task-123")
        assert result["status"] == "completed"

    def test_health(self):
        client = BrainCognitiveClient()
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = b'{"status": "ok"}'
            mock_resp.__enter__ = MagicMock(return_value=mock_resp)
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_resp
            result = client.health()
        assert result["status"] == "ok"

    def test_health_failure(self):
        client = BrainCognitiveClient()
        with patch("urllib.request.urlopen", side_effect=Exception("unreachable")):
            result = client.health()
        assert result["status"] == "unreachable"

    def test_rpc_error_raises(self):
        client = BrainCognitiveClient()
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = b'{"error": {"code": -32600, "message": "Invalid Request"}}'
            mock_resp.__enter__ = MagicMock(return_value=mock_resp)
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_resp
            with pytest.raises(BrainCognitiveError):
                client.trigger_agent("architect")

    def test_rpc_urlerror_raises(self):
        client = BrainCognitiveClient()
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("unreachable")):
            with pytest.raises(BrainCognitiveError):
                client._rpc_call("agent.trigger", {})

    def test_rpc_timeout_raises(self):
        client = BrainCognitiveClient()
        with patch("urllib.request.urlopen", side_effect=TimeoutError("timeout")):
            with pytest.raises(BrainCognitiveError):
                client._rpc_call("agent.trigger", {})

    def test_health_timeout(self):
        client = BrainCognitiveClient()
        with patch("urllib.request.urlopen", side_effect=TimeoutError("timeout")):
            result = client.health()
        assert result["status"] == "timeout"
