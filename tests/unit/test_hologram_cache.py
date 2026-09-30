"""Tests for src/holograms/cache/v1/hologram_cache.py."""

from __future__ import annotations

from src.holograms.cache.v1.hologram_cache import HologramCache


class TestHologramCache:
    def test_set_and_get(self):
        cache = HologramCache()
        cache.set("repo", "zone", {"key": "value"})
        assert cache.get("repo", "zone") == {"key": "value"}

    def test_get_miss_returns_none(self):
        cache = HologramCache()
        assert cache.get("repo", "zone") is None

    def test_clear(self):
        cache = HologramCache()
        cache.set("repo", "zone", {"key": "value"})
        cache.clear()
        assert cache.get("repo", "zone") is None

    def test_stats(self):
        cache = HologramCache()
        cache.set("repo", "zone", {"key": "value"})
        stats = cache.stats()
        assert stats["entries"] == 1
        assert stats["backend"] == "memory"
        assert stats["ttl"] == 300

    def test_key_deterministic(self):
        cache = HologramCache()
        key1 = cache._key("repo", "zone")
        key2 = cache._key("repo", "zone")
        assert key1 == key2
        assert len(key1) == 16
