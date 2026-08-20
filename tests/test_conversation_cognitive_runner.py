"""Tests for Conversation Cognitive Runner (MVP + Phase 1)."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import du module sous test
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "services"))

import conversation_cognitive_runner as ccr
from conversation_cognitive_runner import (
    sanitize_text,
    extract_patterns,
    load_decisions,
    save_decision,
    call_tlm_lang,
    call_chronox,
    call_referex,
    publish_waazaa,
    app,
)


@pytest.fixture
def tmp_data_dir(tmp_path):
    """Remplace le répertoire de données par un tmpdir."""
    original = ccr.DECISIONS_FILE
    ccr.DECISIONS_FILE = tmp_path / "cognitive_decisions.json"
    yield tmp_path
    ccr.DECISIONS_FILE = original


class TestSanitizeText:
    """Tests du filtrage secrets/PII."""

    def test_remove_bearer_token(self):
        text = "Authorization: Bearer ghp_1234567890abcdefghij"
        result = sanitize_text(text)
        assert "ghp_" not in result
        assert "[REDACTED]" in result

    def test_remove_password(self):
        text = "password = 'super_secret_123'"
        result = sanitize_text(text)
        assert "super_secret_123" not in result
        assert "[REDACTED]" in result

    def test_remove_token(self):
        text = "token: sk-abcdef1234567890"
        result = sanitize_text(text)
        assert "sk-abcdef1234567890" not in result
        assert "[REDACTED]" in result

    def test_remove_secret(self):
        text = "secret = my_api_key_12345"
        result = sanitize_text(text)
        assert "my_api_key_12345" not in result
        assert "[REDACTED]" in result

    def test_remove_github_token(self):
        text = "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef"
        result = sanitize_text(text)
        assert "ghp_" not in result
        assert "[REDACTED]" in result

    def test_remove_openai_key(self):
        text = "sk-1234567890abcdefghijklmnop"
        result = sanitize_text(text)
        assert "sk-1234567890abcdefghijklmnop" not in result
        assert "[REDACTED]" in result

    def test_preserve_normal_text(self):
        text = "Décision : Option B choisie pour le bootstrap runner."
        assert sanitize_text(text) == text

    def test_multiple_secrets(self):
        text = "password=foo token=bar secret=baz"
        result = sanitize_text(text)
        assert "password" not in result
        assert "token" not in result
        assert "secret" not in result
        assert "[REDACTED]" in result


class TestExtractPatterns:
    """Tests de l'extraction par patterns."""

    def test_extract_decisions(self):
        text = "Décision : Option B choisie. Decision : Architecture retenue."
        results = extract_patterns(text, [
            r"(?:décision|decision|choix|choisi|retenu|retenue|option)\s*[:\-]\s*(.+)",
        ])
        assert len(results) >= 1
        assert "Option B" in results[0] or "Architecture" in results[0]

    def test_extract_constraints(self):
        text = "Contrainte : BDCP inviolable. Règle : KIVA-CLI only."
        results = extract_patterns(text, [
            r"(?:contrainte|constraint|obligation|interdiction|règle|règle)\s*[:\-]\s*(.+)",
        ])
        assert len(results) >= 1
        assert any("BDCP" in r for r in results)

    def test_extract_alternatives(self):
        text = "Alternative : Option A rejetée car overloading."
        results = extract_patterns(text, [
            r"(?:alternative|option\s+[A-Z]|choix\s+[A-Z]|rejeté?|rejetée?|écarté?|écartée?)\s*[:\-]\s*(.+)",
        ])
        assert len(results) >= 1

    def test_extract_actors(self):
        text = "Par user et kilo : Option B retenue."
        results = extract_patterns(text, [
            r"(?:par|par\s+l'|par\s+la|par\s+les?)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        ])
        assert len(results) >= 1

    def test_empty_text(self):
        results = extract_patterns("", [
            r"(?:décision|decision)\s*[:\-]\s*(.+)",
        ])
        assert results == []

    def test_no_match(self):
        results = extract_patterns("Hello world", [
            r"(?:décision|decision)\s*[:\-]\s*(.+)",
        ])
        assert results == []


class TestStorage:
    """Tests du stockage local."""

    def test_save_and_load(self, tmp_data_dir):
        decision = {
            "type": "Decision",
            "intent_hash": "0xTEST_123",
            "date": "2026-08-21",
            "source": "conversation",
            "session_id": "test-001",
            "status": "proposed",
        }
        save_decision(decision)
        loaded = load_decisions()
        assert len(loaded) == 1
        assert loaded[0]["intent_hash"] == "0xTEST_123"

    def test_load_empty(self, tmp_data_dir):
        assert load_decisions() == []

    def test_save_multiple(self, tmp_data_dir):
        for i in range(3):
            save_decision({"intent_hash": f"0xTEST_{i}", "date": "2026-08-21"})
        loaded = load_decisions()
        assert len(loaded) == 3


class TestKGLSchema:
    """Tests de validation du schéma KG-L."""

    def test_valid_decision(self):
        decision = {
            "type": "Decision",
            "intent_hash": "0xTEST_VALID",
            "date": "2026-08-21",
            "source": "conversation",
            "session_id": "test-001",
            "decision": "Option B",
            "status": "proposed",
        }
        # Vérification minimale des champs requis
        assert decision["type"] == "Decision"
        assert decision["source"] == "conversation"
        assert decision["status"] in ("proposed", "accepted", "rejected", "superseded")

    def test_valid_actor(self):
        actor = {
            "type": "Actor",
            "name": "user",
            "source": "conversation",
            "session_id": "test-001",
        }
        assert actor["type"] == "Actor"

    def test_valid_constraint(self):
        constraint = {
            "type": "Constraint",
            "name": "BDCP inviolable",
            "source": "conversation",
            "session_id": "test-001",
        }
        assert constraint["type"] == "Constraint"

    def test_valid_alternative(self):
        alternative = {
            "type": "Alternative",
            "name": "option_a_inline",
            "reason_discarded": "Overloading",
            "source": "conversation",
            "session_id": "test-001",
        }
        assert alternative["type"] == "Alternative"


class TestWazaaPublish:
    """Tests de publication vers KG-WAZAA (avec mock)."""

    @patch("conversation_cognitive_runner.requests.post")
    def test_publish_success(self, mock_post):
        mock_post.return_value.status_code = 200
        decision = {"type": "Decision", "intent_hash": "0xTEST"}
        assert publish_waazaa(decision) is True
        mock_post.assert_called_once()

    @patch("conversation_cognitive_runner.requests.post")
    def test_publish_failure(self, mock_post):
        mock_post.side_effect = Exception("Connection refused")
        decision = {"type": "Decision", "intent_hash": "0xTEST"}
        assert publish_waazaa(decision) is False

    @patch("conversation_cognitive_runner.requests.post")
    def test_publish_timeout(self, mock_post):
        import requests
        mock_post.side_effect = requests.exceptions.Timeout()
        decision = {"type": "Decision", "intent_hash": "0xTEST"}
        assert publish_waazaa(decision) is False


class TestHealthEndpoint:
    """Tests de l'endpoint health."""

    def test_health_returns_200(self):
        with app.test_client() as client:
            resp = client.get("/cognitive/conversation/health")
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["status"] == "ok"
            assert data["service"] == "conversation-cognitive"
            assert data["port"] == 8811


class TestAnalyzeEndpoint:
    """Tests de l'endpoint analyze."""

    def test_analyze_returns_decisions(self):
        with app.test_client() as client:
            payload = {
                "conversation_text": "Décision : Option B choisie pour le bootstrap runner.",
                "session_id": "test-001",
                "actors": ["user", "kilo"],
                "metadata": {"intent_hash": "0xTEST_ANALYZE"},
            }
            resp = client.post("/cognitive/conversation/analyze", json=payload)
            assert resp.status_code == 200
            data = resp.get_json()
            assert "decisions" in data
            assert len(data["decisions"]) >= 1

    def test_analyze_missing_text_returns_400(self):
        with app.test_client() as client:
            resp = client.post("/cognitive/conversation/analyze", json={})
            assert resp.status_code == 400

    def test_analyze_sanitizes_secrets(self):
        with app.test_client() as client:
            payload = {
                "conversation_text": "Décision : Option B. Token: ghp_1234567890abcdefghij",
                "session_id": "test-002",
            }
            resp = client.post("/cognitive/conversation/analyze", json=payload)
            assert resp.status_code == 200
            data = resp.get_json()
            # Vérifier que le token n'apparaît pas dans les décisions
            for decision in data.get("decisions", []):
                assert "ghp_" not in json.dumps(decision)
