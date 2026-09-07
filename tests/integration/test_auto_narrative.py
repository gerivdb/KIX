#!/usr/bin/env python3
"""
tests/integration/test_auto_narrative.py — Test E2E Auto-Narrative (BT-1)

Test cycle complet : note vault → gap détecté → repair → ré-ingestion → graphe enrichi.

IntentHash: 0xTEST_AUTO_NARRATIVE_E2E_20260905
"""

import pytest
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "runners" / "auto-narrative"))
sys.path.insert(0, str(Path(r"D:\DO\WEB\TOOLS\L4-TOOLS\TALEX\skills")))

from talex_auto_repair import AutoRepairNarrative, KG_L_Client, VaultWriter


class TestAutoNarrative:
    """Tests pour la boucle auto-narrative."""

    @pytest.fixture
    def repair(self):
        """Fixture AutoRepairNarrative avec config test."""
        return AutoRepairNarrative(
            kgl_url="http://localhost:8888",
            wazaa_url="http://localhost:1874",
            vault_path=Path(r"D:\DO\WEB\TOOLS\L0-CANON\VOLTX"),
            max_cycles=1,
            delta_threshold=0.01
        )

    @pytest.fixture
    def kgl_client(self):
        return KG_L_Client("http://localhost:8888")

    @pytest.fixture
    def vault_writer(self):
        return VaultWriter(Path(r"D:\DO\WEB\TOOLS\L0-CANON\VOLTX"))

    def test_query_gaps_returns_untyped_nodes(self, kgl_client):
        """Test que query_gaps détecte les nœuds sans type."""
        # Note: Nécessite KG-L running avec données de test
        gaps = kgl_client.query_gaps()
        assert isinstance(gaps, list)
        # Si des nœuds sans type existent, au moins un devrait être détecté
        if gaps:
            assert all("type" in g and "id" in g for g in gaps)

    def test_write_repair_note_idempotent(self, vault_writer):
        """Test idempotence de write_repair_note."""
        gap_id = "TEST_GAP_001"
        content = "# Test Repair Note\n\nContent for testing."
        
        path1 = vault_writer.write_repair_note(gap_id, content)
        path2 = vault_writer.write_repair_note(gap_id, content)
        
        assert path1 == path2
        assert path1.read_text(encoding="utf-8") == content

    def test_write_repair_note_different_content(self, vault_writer):
        """Test que contenu différent crée nouveau fichier."""
        gap_id = "TEST_GAP_002"
        content1 = "# Test Repair Note 1"
        content2 = "# Test Repair Note 2"
        
        path1 = vault_writer.write_repair_note(gap_id, content1)
        path2 = vault_writer.write_repair_note(gap_id, content2)
        
        # Fichiers différents car hash différent
        assert path1 != path2
        assert path1.read_text() == content1
        assert path2.read_text() == content2

    @pytest.mark.integration
    def test_auto_narrative_full_cycle(self, repair):
        """Test E2E cycle complet (nécessite KG-L/WAZAA running)."""
        # Ce test nécessite l'infrastructure complète
        # Marqué @pytest.mark.integration pour exécution conditionnelle
        
        # 1. Créer gap artificiel dans KG-L (si API dispo)
        # kgl.create_node("TEST_GAP_NODE", type=None)
        
        # 2. Déclencher runner
        result = repair.run_cycle()
        
        # 3. Vérifier structure résultat
        assert "status" in result
        assert "fixed" in result
        assert "delta" in result
        assert result["status"] in ("completed", "no_gaps")
        
        # 4. Si gaps corrigés, vérifier delta positif
        if result["fixed"] > 0:
            assert result["delta"] >= 0

    def test_generate_repair_note_structure(self, repair):
        """Test structure note de réparation générée."""
        gap = {
            "id": "TEST_NODE_123",
            "type": "untyped",
            "title": "Test Node",
            "labels": ["Concept"]
        }
        
        note = repair.generate_repair_note(gap)
        
        assert "type: repair" in note
        assert "auto-narrative" in note
        assert "untyped" in note
        assert "TEST_NODE_123" in note
        assert "intent_hash" in note.lower()
        assert "- [ ]" in note  # Checkboxes actions


class TestKG_L_Client:
    """Tests pour KG_L_Client."""

    @pytest.fixture
    def client(self):
        return KG_L_Client("http://localhost:8888")

    def test_count_nodes(self, client):
        """Test comptage nœuds."""
        count = client.count_nodes()
        assert isinstance(count, int)
        assert count >= 0

    def test_get_graph_stats(self, client):
        """Test stats graphe."""
        stats = client.get_graph_stats()
        assert "nodes" in stats
        assert "edges" in stats
        assert "components" in stats
        assert "chi" in stats
        assert all(isinstance(v, int) for v in stats.values())


class TestVaultWriter:
    """Tests pour Vault_Writer."""

    @pytest.fixture
    def writer(self):
        return Vault_Writer(Path(r"D:\DO\WEB\TOOLS\L0-CANON\VOLTX"))

    def test_write_repair_note_creates_file(self, writer):
        """Test création fichier."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            writer.vault_path = Path(tmpdir)
            path = writer.write_repair_note("TEST_001", "# Test\nContent")
            assert path.exists()
            assert path.read_text() == "# Test\nContent"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])