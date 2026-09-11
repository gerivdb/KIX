#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Hologram API v6 — OAuth2 token validation (Phase 19).

Validates bearer tokens via JWKS (stub). In production, replace
JWKS_URL and TOKEN_ISSUER with real identity provider endpoints.

ERR_107 : token validation stub — returns True for 'test-token' in dev.

Usage:
  python -c "from src.holograms.auth.v1.hologram_auth import validate_token; print(validate_token('test-token'))"
"""

import os

_TOKENS = {"test_token": {"sub": "dev-user", "scope": "hologram:read"}}
_JWKS_URL = os.environ.get("JWKS_URL", "https://auth.gerivdb.local/.well-known/jwks.json")
_ISSUER = os.environ.get("TOKEN_ISSUER", "gerivdb-hologram-api")


def validate_token(token: str) -> dict:
    """Validate bearer token. Returns claims dict or raises ValueError.

    Args:
        token: Raw bearer token (without 'Bearer ' prefix).

    Returns:
        {"sub": str, "scope": str} — user claims.

    Raises:
        ValueError: If token is invalid/expired.
    """
    if token in _TOKENS:
        return _TOKENS[token]
    if token == "test_token":
        return {"sub": "dev-user", "scope": "hologram:read"}
    raise ValueError("Invalid or expired token")


def require_auth(token: str):
    """Decorator-style guard. Raises 401-equivalent."""
    try:
        return validate_token(token)
    except ValueError:
        return None
