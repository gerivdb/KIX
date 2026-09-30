"""Tests for src/auth.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.auth import create_token, decode_token, login_required, requires_capability, _load_users


class TestCreateToken:
    def test_create_token(self):
        token = create_token("admin", "admin")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_token_valid(self):
        token = create_token("admin", "admin")
        payload = decode_token(token)
        assert payload["sub"] == "admin"
        assert payload["role"] == "admin"

    def test_decode_token_invalid(self):
        assert decode_token("invalid") is None


class TestLoginRequired:
    def test_missing_token(self):
        decorator = login_required()
        mock_request = MagicMock()
        mock_request.headers.get.return_value = ""
        with patch("src.auth.request", mock_request):
            with patch("src.auth.jsonify", lambda payload: (payload, 401)):
                response = decorator(lambda: "ok")()
        assert response[1] == 401

    def test_valid_token(self):
        decorator = login_required()
        token = create_token("admin", "admin")
        mock_request = MagicMock()
        mock_request.headers.get.return_value = f"Bearer {token}"
        with patch("src.auth.request", mock_request):
            response = decorator(lambda: "ok")
            assert response() == "ok"

    def test_invalid_token(self):
        decorator = login_required()
        mock_request = MagicMock()
        mock_request.headers.get.return_value = "Bearer invalid"
        with patch("src.auth.request", mock_request):
            with patch("src.auth.jsonify", lambda payload: (payload, 401)):
                response = decorator(lambda: "ok")()
        assert response[1] == 401


class TestRequiresCapability:
    def test_missing_token(self):
        decorator = requires_capability("runner:start")
        mock_request = MagicMock()
        mock_request.headers.get.return_value = ""
        with patch("src.auth.request", mock_request):
            with patch("src.auth.jsonify", lambda payload: (payload, 401)):
                response = decorator(lambda: "ok")()
        assert response[1] == 401

    def test_valid_token_with_capability(self, monkeypatch):
        monkeypatch.setattr("src.auth.check_capability", lambda role, cap: True)
        decorator = requires_capability("runner:start")
        token = create_token("admin", "admin")
        mock_request = MagicMock()
        mock_request.headers.get.return_value = f"Bearer {token}"
        with patch("src.auth.request", mock_request):
            response = decorator(lambda: "ok")
            assert response() == "ok"

    def test_valid_token_without_capability(self, monkeypatch):
        monkeypatch.setattr("src.auth.check_capability", lambda role, cap: False)
        decorator = requires_capability("runner:start")
        token = create_token("viewer", "viewer")
        mock_request = MagicMock()
        mock_request.headers.get.return_value = f"Bearer {token}"
        with patch("src.auth.request", mock_request):
            with patch("src.auth.jsonify", lambda payload: (payload, 403)):
                response = decorator(lambda: "ok")()
        assert response[1] == 403


class TestLoadUsers:
    def test_load_users_from_env(self, monkeypatch):
        import json

        env_users = json.dumps({"alice": {"password": "secret", "role": "admin"}})
        monkeypatch.setenv("KIX_USERS", env_users)
        users = _load_users()
        assert "alice" in users
        assert users["alice"]["role"] == "admin"

    def test_load_users_default_when_no_env(self, monkeypatch):
        monkeypatch.delenv("KIX_USERS", raising=False)
        users = _load_users()
        assert "admin" in users
        assert "operator" in users
        assert "viewer" in users


class TestRequiresCapabilityInvalidToken:
    def test_invalid_token_returns_401(self):
        decorator = requires_capability("runner:start")
        mock_request = MagicMock()
        mock_request.headers.get.return_value = "Bearer invalid"
        with patch("src.auth.request", mock_request):
            with patch("src.auth.jsonify", lambda payload: (payload, 401)):
                response = decorator(lambda: "ok")()
        assert response[1] == 401
