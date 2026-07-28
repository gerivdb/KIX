"""JWT-based authentication and RBAC for KIX."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from datetime import timedelta
from functools import wraps
from typing import Optional

import jwt
from flask import request, jsonify


# Default users for development. Override via KIX_USERS env var (JSON).
_USERS = {
    "admin": {"password": "admin123", "role": "admin"},
    "operator": {"password": "operator123", "role": "operator"},
    "viewer": {"password": "viewer123", "role": "viewer"},
}

JWT_SECRET = os.environ.get("KIX_JWT_SECRET", "dev-secret-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 12


def _load_users() -> dict[str, dict[str, str]]:
    env_users = os.environ.get("KIX_USERS")
    if env_users:
        import json

        return json.loads(env_users)
    return _USERS


def create_token(username: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": username,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=JWT_EXPIRATION_HOURS)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None


def login_required(roles: Optional[list[str]] = None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return jsonify({"error": "missing_token"}), 401
            token = auth_header.split(" ", 1)[1]
            payload = decode_token(token)
            if not payload:
                return jsonify({"error": "invalid_token"}), 401
            user_role = payload.get("role")
            if roles and user_role not in roles:
                return jsonify({"error": "forbidden", "required_roles": roles}), 403
            request.user = payload
            return f(*args, **kwargs)

        return wrapper

    return decorator
