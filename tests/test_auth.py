"""Tests for KIX authentication and RBAC."""

import pytest
from src.auth import create_token, decode_token, _load_users, login_required


def test_create_and_decode_token() -> None:
    token = create_token("admin", "admin")
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "admin"
    assert payload["role"] == "admin"
    assert "exp" in payload
    assert "iat" in payload


def test_decode_invalid_token_returns_none() -> None:
    assert decode_token("invalid-token") is None
    assert decode_token("") is None


def test_load_users_returns_defaults() -> None:
    users = _load_users()
    assert "admin" in users
    assert users["admin"]["role"] == "admin"
    assert "operator" in users
    assert "viewer" in users


def test_login_endpoint_returns_token(client) -> None:
    resp = client.post(
        "/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert "access_token" in data
    assert data["role"] == "admin"
    assert data["username"] == "admin"


def test_login_endpoint_rejects_bad_credentials(client) -> None:
    resp = client.post(
        "/login",
        json={"username": "admin", "password": "wrong"},
    )
    assert resp.status_code == 401
    data = resp.get_json()
    assert data["error"] == "invalid_credentials"


def test_protected_endpoint_requires_token(client) -> None:
    resp = client.get("/audit")
    assert resp.status_code == 401
    data = resp.get_json()
    assert data["error"] == "missing_token"


def test_protected_endpoint_rejects_wrong_role(client) -> None:
    token = create_token("viewer", "viewer")
    resp = client.get(
        "/audit",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
    data = resp.get_json()
    assert data["error"] == "forbidden"


def test_protected_endpoint_accepts_valid_token(client) -> None:
    token = create_token("admin", "admin")
    resp = client.get(
        "/audit",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert "audit" in data
