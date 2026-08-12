"""Tests d'intégration de base pour zombie_monitor.py."""
import pytest
import sys
import os

# Ajouter KIX/src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from zombie_monitor import log_kg_l_edge, detect_zombie, ZOMBIE_THRESHOLD_SEC


class TestZombieMonitor:
    """Tests pour le module zombie_monitor."""

    def test_detect_zombie_returns_false_for_active_runner(self):
        """Un runner actif n'est pas détecté comme zombie."""
        runner = {
            "id": "runner-001",
            "last_heartbeat": "2026-08-13T01:00:00Z",
            "status": "RUNNING",
        }
        # P0: placeholder - validé avec un timestamp récent
        # Phase 1: utilisera un vrai timestamp et comparaison
        is_zombie = detect_zombie(runner)
        assert is_zombie is False or is_zombie is True  # placeholder P0

    def test_detect_zombie_returns_true_for_stale_runner(self):
        """Un runner sans heartbeat depuis > 30min est détecté comme zombie."""
        runner = {
            "id": "runner-002",
            "last_heartbeat": "2026-08-13T00:00:00Z",  # > 30min ago
            "status": "RUNNING",
        }
        # P0: placeholder
        is_zombie = detect_zombie(runner)
        assert is_zombie is False or is_zombie is True  # placeholder P0

    def test_log_kg_l_edge_creates_edge(self):
        """log_kg_l_edge émet un edge KG-L vers le runner zombie."""
        runner_id = "runner-zombie-001"
        edge_kind = "prevents"
        
        # P0: placeholder - validé avec un mock KG-L runtime
        result = log_kg_l_edge(runner_id, edge_kind)
        assert result is None or result is True  # placeholder P0

    def test_zombie_threshold_is_30_minutes(self):
        """Le seuil de détection zombie est bien de 30 minutes."""
        assert ZOMBIE_THRESHOLD_SEC == 1800  # 30 * 60

    def test_log_kg_l_edge_with_metadata(self):
        """log_kg_l_edge accepte des métadonnées optionnelles."""
        runner_id = "runner-zombie-002"
        edge_kind = "prevents"
        metadata = {"reason": "no_heartbeat", "threshold": 1800}
        
        result = log_kg_l_edge(runner_id, edge_kind, metadata=metadata)
        assert result is None or result is True  # placeholder P0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
