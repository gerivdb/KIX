"""Tests for src/hermes_memory_client.py."""

from __future__ import annotations

import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from src.hermes_memory_client import HermesMemoryClient, HermesMemoryError


class TestHermesMemoryClient:
    def test_read_memory(self):
        client = HermesMemoryClient()
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = b'{"key": "test", "value": {"data": "hello"}}'
            mock_resp.__enter__ = MagicMock(return_value=mock_resp)
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_resp
            result = client.read_memory("test")
        assert result["value"]["data"] == "hello"

    def test_write_memory(self):
        client = HermesMemoryClient()
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = b'{"status": "ok"}'
            mock_resp.__enter__ = MagicMock(return_value=mock_resp)
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_resp
            result = client.write_memory("test", {"data": "hello"})
        assert result is True

    def test_get_recommended_skills(self):
        client = HermesMemoryClient()
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = b'{"skills": ["skill-1", "skill-2"]}'
            mock_resp.__enter__ = MagicMock(return_value=mock_resp)
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_resp
            result = client.get_recommended_skills()
        assert result == ["skill-1", "skill-2"]

    def test_publish_fact(self):
        client = HermesMemoryClient()
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = b'{"status": "published", "id": "fact-123"}'
            mock_resp.__enter__ = MagicMock(return_value=mock_resp)
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_resp
            result = client.publish_fact({"type": "event", "data": "test"})
        assert result is True

    def test_health(self):
        client = HermesMemoryClient()
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = b'{"status": "ok"}'
            mock_resp.__enter__ = MagicMock(return_value=mock_resp)
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_resp
            result = client.health()
        assert result["status"] == "ok"

    def test_health_failure(self):
        client = HermesMemoryClient()
        with patch("urllib.request.urlopen", side_effect=Exception("unreachable")):
            result = client.health()
        assert result["status"] == "unreachable"

    def test_read_memory_urlerror(self):
        client = HermesMemoryClient()
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("unreachable")):
            with pytest.raises(HermesMemoryError):
                client.read_memory("test")

    def test_write_memory_urlerror(self):
        client = HermesMemoryClient()
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("unreachable")):
            with pytest.raises(HermesMemoryError):
                client.write_memory("test", {"data": "hello"})

    def test_get_recommended_skills_urlerror(self):
        client = HermesMemoryClient()
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("unreachable")):
            with pytest.raises(HermesMemoryError):
                client.get_recommended_skills()

    def test_publish_fact_urlerror(self):
        client = HermesMemoryClient()
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("unreachable")):
            with pytest.raises(HermesMemoryError):
                client.publish_fact({"type": "event"})

    def test_read_memory_timeout(self):
        client = HermesMemoryClient()
        with patch("urllib.request.urlopen", side_effect=TimeoutError("timeout")):
            with pytest.raises(HermesMemoryError):
                client.read_memory("test")

    def test_write_memory_timeout(self):
        client = HermesMemoryClient()
        with patch("urllib.request.urlopen", side_effect=TimeoutError("timeout")):
            with pytest.raises(HermesMemoryError):
                client.write_memory("test", {"data": "hello"})

    def test_health_hermes_memory_error(self):
        client = HermesMemoryClient()
        with patch.object(client, "_get", side_effect=HermesMemoryError("hermes error")):
            result = client.health()
        assert result["status"] == "unreachable"
