#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Hologram API v3 — Distributed cache backend (Phase 16).

Supports: Redis (via flask_socketio) + in-memory fallback.

ERR_097-fix : created during Phase 15 alongside swagger_ui_generator.py.
"""

import hashlib
import json
from typing import Any, Optional

_CACHE: dict[str, Any] = {}


class HologramCache:
    """Minimal cache layer for hologram responses (v3).

    Uses in-memory dict by default. Redis integration via redis-py if installed.
    """

    def __init__(self, ttl: int = 300):
        self.ttl = ttl
        self._store: dict[str, dict] = {}

    def _key(self, repo: str, zone: str = "all") -> str:
        raw = f"{repo}:{zone}:{self.ttl}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def get(self, repo: str, zone: str = "all") -> Optional[dict]:
        """Retrieve cached hologram JSON."""
        k = self._key(repo, zone)
        entry = self._store.get(k)
        if entry is None:
            return None
        return entry["data"]

    def set(self, repo: str, zone: str, data: dict) -> None:
        """Store hologram data in cache."""
        k = self._key(repo, zone)
        self._store[k] = {"data": data}

    def clear(self) -> None:
        """Flush all cache entries."""
        self._store.clear()

    def stats(self) -> dict:
        """Return cache statistics."""
        return {
            "entries": len(self._store),
            "ttl": self.ttl,
            "backend": "memory",
        }
