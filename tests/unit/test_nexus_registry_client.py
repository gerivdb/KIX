"""Tests for src/nexus_registry_client.py."""

from __future__ import annotations

import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from src.nexus_registry_client import NexusRegistryClient, NexusRegistryError


class TestNexusRegistryClient:
    def test_get_registry(self):
        client = NexusRegistryClient()
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = b'{"name": "test-registry", "version": "1.0"}'
            mock_resp.__enter__ = MagicMock(return_value=mock_resp)
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_resp
            result = client.get_registry("test-registry")
        assert result["name"] == "test-registry"

    def test_list_repos(self):
        client = NexusRegistryClient()
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = b'{"repos": [{"name": "KIX"}, {"name": "BRAIN"}]}'
            mock_resp.__enter__ = MagicMock(return_value=mock_resp)
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_resp
            result = client.list_repos()
        assert len(result) == 2
        assert result[0]["name"] == "KIX"

    def test_get_repo(self):
        client = NexusRegistryClient()
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = b'{"name": "KIX", "status": "active"}'
            mock_resp.__enter__ = MagicMock(return_value=mock_resp)
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_resp
            result = client.get_repo("gerivdb/KIX")
        assert result["status"] == "active"

    def test_health(self):
        client = NexusRegistryClient()
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = b'{"status": "ok"}'
            mock_resp.__enter__ = MagicMock(return_value=mock_resp)
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_resp
            result = client.health()
        assert result["status"] == "ok"

    def test_health_failure(self):
        client = NexusRegistryClient()
        with patch("urllib.request.urlopen", side_effect=Exception("unreachable")):
            result = client.health()
        assert result["status"] == "unreachable"

    def test_get_registry_urlerror(self):
        client = NexusRegistryClient()
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("unreachable")):
            with pytest.raises(NexusRegistryError):
                client.get_registry("test")

    def test_list_repos_urlerror(self):
        client = NexusRegistryClient()
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("unreachable")):
            with pytest.raises(NexusRegistryError):
                client.list_repos()

    def test_get_repo_urlerror(self):
        client = NexusRegistryClient()
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("unreachable")):
            with pytest.raises(NexusRegistryError):
                client.get_repo("gerivdb/KIX")

    def test_get_registry_timeout(self):
        client = NexusRegistryClient()
        with patch("urllib.request.urlopen", side_effect=TimeoutError("timeout")):
            with pytest.raises(NexusRegistryError):
                client.get_registry("test")
