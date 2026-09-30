"""Tests for src/trix_client.py."""

from __future__ import annotations

import json
import urllib.error
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.trix_client import _request, get_worktree_locks, health_check, release_lock, kiva_run, kiva_stop, kiva_list, kiva_snapshot, kiva_restore


def _make_resp(payload):
    mock_resp = MagicMock()
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_resp.read.return_value = json.dumps(payload).encode("utf-8")
    return mock_resp


class TestRequest:
    def test_get_request_success(self):
        with patch("src.trix_client.urllib.request.urlopen", return_value=_make_resp({"ok": True})):
            result = _request("http://127.0.0.1:8742/health")
        assert result == {"ok": True}

    def test_post_request_success(self):
        with patch("src.trix_client.urllib.request.urlopen", return_value=_make_resp({"ok": True})):
            result = _request("http://127.0.0.1:8742/git/locks/release", {"branch": "main", "agent_id": "a1"})
        assert result == {"ok": True}

    def test_request_url_error(self):
        with patch("src.trix_client.urllib.request.urlopen", side_effect=urllib.error.URLError("connection refused")):
            result = _request("http://127.0.0.1:8742/health")
        assert "error" in result

    def test_request_json_decode_error(self):
        with patch("src.trix_client.urllib.request.urlopen", return_value=_make_resp({"ok": True})):
            with patch("src.trix_client.json.loads", side_effect=json.JSONDecodeError("Expecting value", "not-json", 0)):
                result = _request("http://127.0.0.1:8742/health")
        assert "error" in result


class TestTrixClientFunctions:
    def test_release_lock(self):
        with patch("src.trix_client._request", return_value={"ok": True}) as mock_req:
            result = release_lock("main", "agent-1")
        mock_req.assert_called_once_with("http://127.0.0.1:8742/git/locks/release", {"branch": "main", "agent_id": "agent-1"})
        assert result == {"ok": True}

    def test_get_worktree_locks(self):
        with patch("src.trix_client._request", return_value={"locks": []}) as mock_req:
            result = get_worktree_locks()
        mock_req.assert_called_once_with("http://127.0.0.1:8742/git/locks/worktrees")
        assert result == {"locks": []}

    def test_health_check_ok(self):
        with patch("src.trix_client._request", return_value={"status": "ok"}):
            assert health_check() is True

    def test_health_check_error(self):
        with patch("src.trix_client._request", return_value={"error": "timeout"}):
            assert health_check() is False


class TestTrixClientExtended:
    def test_kiva_run(self):
        with patch("src.trix_client._request", return_value={"container": "trixd-001"}) as mock_req:
            result = kiva_run({"image": "trixd", "cpu": 4})
        mock_req.assert_called_once_with("http://127.0.0.1:8742/kiva-run", {"image": "trixd", "cpu": 4})
        assert result["container"] == "trixd-001"

    def test_kiva_stop(self):
        with patch("src.trix_client._request", return_value={"stopped": True}) as mock_req:
            result = kiva_stop("trixd-001")
        mock_req.assert_called_once_with("http://127.0.0.1:8742/containers/trixd-001/stop")
        assert result["stopped"] is True

    def test_kiva_list(self):
        with patch("src.trix_client._request", return_value={"containers": []}) as mock_req:
            result = kiva_list()
        mock_req.assert_called_once_with("http://127.0.0.1:8742/kiva-list")
        assert result["containers"] == []

    def test_kiva_snapshot(self):
        with patch("src.trix_client._request", return_value={"snapshot": "snap-123"}) as mock_req:
            result = kiva_snapshot("trixd-001")
        mock_req.assert_called_once_with("http://127.0.0.1:8742/containers/trixd-001/snapshot")
        assert result["snapshot"] == "snap-123"

    def test_kiva_restore(self):
        with patch("src.trix_client._request", return_value={"restored": True}) as mock_req:
            result = kiva_restore("trixd-001", "snap-123")
        mock_req.assert_called_once_with("http://127.0.0.1:8742/containers/trixd-001/restore", {"snapshot": "snap-123"})
        assert result["restored"] is True
