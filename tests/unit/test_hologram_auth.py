"""Tests for src/holograms/auth/v1/hologram_auth.py."""

from __future__ import annotations

import pytest

from src.holograms.auth.v1.hologram_auth import require_auth, validate_token


class TestValidateToken:
    def test_known_token(self):
        assert validate_token("test_token") == {"sub": "dev-user", "scope": "hologram:read"}

    def test_invalid_token(self):
        with pytest.raises(ValueError):
            validate_token("invalid")


class TestRequireAuth:
    def test_valid_token(self):
        assert require_auth("test_token") == {"sub": "dev-user", "scope": "hologram:read"}

    def test_invalid_token_returns_none(self):
        assert require_auth("invalid") is None
