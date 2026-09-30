"""Tests for src/governance_hub_client.py."""

from __future__ import annotations

import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from src.governance_hub_client import GovernanceHubClient, GovernanceHubError


class TestGovernanceHubClient:
    def test_get_registry_local(self, tmp_path, monkeypatch):
        registry_file = tmp_path / "known_repositories.yaml"
        registry_file.write_text("repos:\n  - repo: gerivdb/KIX\n")
        client = GovernanceHubClient(local_path=registry_file)
        result = client.get_registry("repos")
        assert result[0]["repo"] == "gerivdb/KIX"

    def test_get_registry_remote(self):
        client = GovernanceHubClient()
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = b'{"repos": []}'
            mock_resp.__enter__ = MagicMock(return_value=mock_resp)
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_resp
            result = client.get_registry("repos")
        assert result["repos"] == []

    def test_validate_adr(self):
        client = GovernanceHubClient()
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = b'{"valid": true}'
            mock_resp.__enter__ = MagicMock(return_value=mock_resp)
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_resp
            result = client.validate_adr("ADR-001.md")
        assert result is True

    def test_validate_prd_moc(self):
        client = GovernanceHubClient()
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = b'{"valid": true}'
            mock_resp.__enter__ = MagicMock(return_value=mock_resp)
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_resp
            result = client.validate_prd_moc("PRD-MOC-001.md")
        assert result is True

    def test_health_local(self, tmp_path, monkeypatch):
        registry_file = tmp_path / "known_repositories.yaml"
        registry_file.write_text("repos:\n")
        client = GovernanceHubClient(local_path=registry_file)
        result = client.health()
        assert result["status"] == "ok"
        assert result["mode"] == "local"

    def test_health_remote(self):
        client = GovernanceHubClient()
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = b'{"status": "ok"}'
            mock_resp.__enter__ = MagicMock(return_value=mock_resp)
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_resp
            result = client.health()
        assert result["status"] == "ok"

    def test_get_registry_local_missing_key(self, tmp_path, monkeypatch):
        registry_file = tmp_path / "known_repositories.yaml"
        registry_file.write_text("repos:\n  - repo: gerivdb/KIX\n")
        client = GovernanceHubClient(local_path=registry_file)
        with pytest.raises(GovernanceHubError):
            client.get_registry("missing")

    def test_get_urlerror_raises(self):
        client = GovernanceHubClient()
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("unreachable")):
            with pytest.raises(GovernanceHubError):
                client._get("/health")

    def test_get_timeout_raises(self):
        client = GovernanceHubClient()
        with patch("urllib.request.urlopen", side_effect=TimeoutError("timeout")):
            with pytest.raises(GovernanceHubError):
                client._get("/health")

    def test_post_urlerror_raises(self):
        client = GovernanceHubClient()
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("unreachable")):
            with pytest.raises(GovernanceHubError):
                client._post("/validate/adr", {"path": "ADR-001.md"})

    def test_post_timeout_raises(self):
        client = GovernanceHubClient()
        with patch("urllib.request.urlopen", side_effect=TimeoutError("timeout")):
            with pytest.raises(GovernanceHubError):
                client._post("/validate/adr", {"path": "ADR-001.md"})

    def test_health_remote_governance_hub_error(self):
        client = GovernanceHubClient()
        with patch.object(client, "_get", side_effect=GovernanceHubError("remote error")):
            result = client.health()
        assert result["status"] == "unreachable"
        assert result["mode"] == "remote"
