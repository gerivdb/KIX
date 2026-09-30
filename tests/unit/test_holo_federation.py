"""Tests for src/holograms/federation/v1/holo_federation.py."""

from __future__ import annotations

import time

from src.holograms.federation.v1.holo_federation import HoloFederation


class TestHoloFederation:
    def test_sync_all(self):
        federation = HoloFederation()
        status = federation.sync()
        assert status["status"] == "ok"
        assert set(status["peers"]) == {"KIX", "VERSES", "CTULU", "GOVERNANCE-HUB"}
        assert set(status["synced"]) == {"KIX", "VERSES", "CTULU", "GOVERNANCE-HUB"}
        assert status["last_sync"] > 0

    def test_sync_single_repo(self):
        federation = HoloFederation()
        status = federation.sync("KIX")
        assert status["synced"] == ["KIX"]
        assert status["last_sync"] > 0

    def test_get_peer_state_found(self):
        federation = HoloFederation()
        federation.sync("KIX")
        state = federation.get_peer_state("KIX")
        assert state["synced"] is True

    def test_get_peer_state_missing(self):
        federation = HoloFederation()
        assert federation.get_peer_state("UNKNOWN") is None
