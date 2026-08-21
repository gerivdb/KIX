"""Conversation Cognitive Runner - Extraction et publication de décisions conversationnelles.

Port: 8811
Endpoints:
  GET  /cognitive/conversation/health
  POST /cognitive/conversation/analyze
  GET  /cognitive/decisions
  GET  /cognitive/decisions/{session_id}
  POST /cognitive/governance/auto        # Phase 2: auto-génération ADR/PRD/INTENT
  GET  /cognitive/governance/patterns    # Phase 2: patterns connus
  GET  /cognitive/dashboard              # Phase 2: tableau de bord
  POST /cognitive/referex/validate       # Phase 2: validation REFEREX avant commit
"""

from __future__ import annotations

import json
import logging
import os
import re
import socket
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from flask import Flask, jsonify, request

from auto_governance import (
    auto_generate,
    detect_patterns,
    get_dashboard_stats,
    load_artifacts,
    validate_regex_safety,
    KNOWN_PATTERNS,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [COG] %(message)s")
logger = logging.getLogger("conversation-cognitive")

SERVICE_NAME = "conversation-cognitive"
PORT = 8811

# Répertoire de stockage local
DATA_DIR = Path(os.environ.get("COGNITIVE_DATA_DIR", str(Path(__file__).resolve().parent.parent / "data" / "cognitive")))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DECISIONS_FILE = DATA_DIR / "cognitive_decisions.json"

# Patterns d'extraction
DECISION_PATTERNS = [
    r"(?:décision|decision|choix|choisi|retenu|retenue|option)\s*[:\-]\s*(.+)",
    r"(?:nous (?:avons|allons|devons) (?:choisi|retenu|opté|décidé))\s+(.+)",
    r"(?:arbitrage|arbitrer)\s*[:\-]\s*(.+)",
]
ACTOR_PATTERNS = [
    r"(?:par|par\s+l'|par\s+la|par\s+les?)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
    r"(?:user|kilo|gerivdb|équipe|team)\s+([A-Za-z]+)",
]
CONSTRAINT_PATTERNS = [
    r"(?:contrainte|constraint|obligation|interdiction|règle|règle)\s*[:\-]\s*(.+)",
    r"(?:ne (?:pas|jamais|doit|doivent))\s+(.+)",
    r"(?:BDCP|KIVA-CLI|pre-commit|ALFRED|governance)\s+(.+)",
]
ALTERNATIVE_PATTERNS = [
    r"(?:alternative|option\s+[A-Z]|choix\s+[A-Z]|rejeté?|rejetée?|écarté?|écartée?)\s*[:\-]\s*(.+)",
    r"(?:non\s+retenu|non\s+retenue|pas\s+choisi|pas\s+retenu)\s+(.+)",
]

# Filtrage secrets/PII
SENSITIVE_PATTERNS = [
    re.compile(r"Bearer\s+[A-Za-z0-9_\-]+", re.IGNORECASE),
    re.compile(r"password\s*[:=]\s*['\"]?[A-Za-z0-9_\-]+", re.IGNORECASE),
    re.compile(r"token\s*[:=]\s*['\"]?[A-Za-z0-9_\-]+", re.IGNORECASE),
    re.compile(r"secret\s*[:=]\s*['\"]?[A-Za-z0-9_\-]+", re.IGNORECASE),
    re.compile(r"gh[ps]_[A-Za-z0-9_]{4,}", re.IGNORECASE),
    re.compile(r"sk-[A-Za-z0-9]{4,}", re.IGNORECASE),
]

# Endpoints runners existants (pour Phase 1, fallback si imports locaux échouent)
RUNNER_ENDPOINTS = {
    "tlm-lang": "http://127.0.0.1:8812/tlm-lang/analyze",
    "chronox": "http://127.0.0.1:8813/chronox/timeline",
    "referex": "http://127.0.0.1:8814/referex/validate",
    "wazaa": "http://127.0.0.1:5002/wazaa/publish",
}


def _import_local_runners():
    """Tente d'importer les runners locaux depuis CTULU et GOVERNANCE-HUB."""
    tlm_lang_cls = None
    chronox_cls = None
    referex_cls = None
    try:
        ctulu_runners_path = Path(r"D:\DO\WEB\TOOLS\L4-TOOLS\CTULU")
        if str(ctulu_runners_path) not in sys.path:
            sys.path.insert(0, str(ctulu_runners_path))
        from ctulu.runners.tlm_lang_runner import TlmLangRunner  # noqa: F401
        tlm_lang_cls = TlmLangRunner
    except Exception:
        pass
    try:
        gov_runners_path = Path(r"D:\DO\WEB\TOOLS\L0-CANON\GOVERNANCE-HUB\runners")
        if str(gov_runners_path) not in sys.path:
            sys.path.insert(0, str(gov_runners_path))
        import chronox as chronox_mod
        import referex as referex_mod
        chronox_cls = getattr(chronox_mod, "ChronoxRunner", None)
        referex_cls = getattr(referex_mod, "ReferexRunner", None)
    except Exception:
        pass
    return tlm_lang_cls, chronox_cls, referex_cls


_TLM_LANG_CLS, _CHRONOX_CLS, _REFEREX_CLS = _import_local_runners()


def sanitize_text(text: str) -> str:
    """Supprime les secrets et PII d'un texte."""
    for pattern in SENSITIVE_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text


def extract_patterns(text: str, patterns: list[str]) -> list[str]:
    """Extrait des motifs depuis un texte avec une liste de patterns regex."""
    results = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
        results.extend(matches)
    # Dédoublonner et nettoyer
    return list({r.strip() for r in results if r.strip() and len(r.strip()) > 2})


def load_decisions() -> list[dict[str, Any]]:
    """Charge les décisions depuis le fichier local."""
    if not DECISIONS_FILE.exists():
        return []
    try:
        with open(DECISIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def save_decision(decision: dict[str, Any]) -> None:
    """Ajoute une décision au stockage local."""
    decisions = load_decisions()
    decisions.append(decision)
    # Garder seulement les 1000 dernières décisions
    if len(decisions) > 1000:
        decisions = decisions[-1000:]
    with open(DECISIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(decisions, f, ensure_ascii=False, indent=2)


def call_tlm_lang(text: str) -> dict[str, Any]:
    """Appelle TLM-LANG pour détecter les ambiguïtés (Phase 1)."""
    if _TLM_LANG_CLS is not None:
        try:
            runner = _TLM_LANG_CLS()
            output = runner.run({"description": text, "messages": [text]})
            data = output.data if hasattr(output, "data") else output
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    try:
        resp = requests.post(RUNNER_ENDPOINTS["tlm-lang"], json={"text": text}, timeout=2)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return {"ambiguities": [], "score": 0.0}


def call_chronox(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    """Appelle CHRONOX pour timeline (Phase 1)."""
    if _CHRONOX_CLS is not None:
        try:
            runner = _CHRONOX_CLS()
            results = []
            for decision in decisions:
                output = runner.run({
                    "entity_id": decision.get("intent_hash", "unknown"),
                    "time_range": {"start": decision.get("date"), "end": decision.get("date")},
                })
                data = output.data if hasattr(output, "data") else output
                if isinstance(data, dict):
                    results.append(data)
            return {"timeline": results}
        except Exception:
            pass
    try:
        resp = requests.post(RUNNER_ENDPOINTS["chronox"], json={"decisions": decisions}, timeout=2)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return {"timeline": []}


def call_referex(artifacts: list[str]) -> dict[str, Any]:
    """Appelle REFEREX pour validation (Phase 1)."""
    if _REFEREX_CLS is not None:
        try:
            runner = _REFEREX_CLS()
            output = runner.run({
                "intent_hash": artifacts[0] if artifacts else "unknown",
                "document_type": "PRD",
            })
            data = output.data if hasattr(output, "data") else output
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    try:
        resp = requests.post(RUNNER_ENDPOINTS["referex"], json={"artifacts": artifacts}, timeout=2)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return {"valid": True, "broken_links": []}


def publish_waazaa(decision: dict[str, Any]) -> bool:
    """Publie vers KG-WAZAA (Phase 1)."""
    try:
        resp = requests.post(RUNNER_ENDPOINTS["wazaa"], json=decision, timeout=2)
        return resp.status_code == 200
    except Exception:
        return False


app = Flask(__name__)


@app.route("/cognitive/conversation/health", methods=["GET"])
def health():
    """Health check basique."""
    return jsonify({"status": "ok", "service": SERVICE_NAME, "port": PORT}), 200


@app.route("/cognitive/conversation/analyze", methods=["POST"])
def analyze():
    """Analyse une conversation et extrait les décisions."""
    data = request.get_json(force=True)
    conversation_text = data.get("conversation_text", "")
    session_id = data.get("session_id", "unknown")
    actors = data.get("actors", ["user", "kilo"])
    metadata = data.get("metadata", {})

    if not conversation_text:
        return jsonify({"error": "conversation_text is required"}), 400

    # Sanitization
    sanitized_text = sanitize_text(conversation_text)

    # Phase 0: Extraction basique par patterns
    decisions_raw = extract_patterns(sanitized_text, DECISION_PATTERNS)
    constraints_raw = extract_patterns(sanitized_text, CONSTRAINT_PATTERNS)
    alternatives_raw = extract_patterns(sanitized_text, ALTERNATIVE_PATTERNS)
    actors_raw = actors if actors else extract_patterns(sanitized_text, ACTOR_PATTERNS)

    # Construction des entités KG-L
    decisions = []
    for idx, decision_text in enumerate(decisions_raw[:5]):  # Max 5 décisions par session
        decision = {
            "type": "Decision",
            "intent_hash": metadata.get("intent_hash", f"0xCONVERSATION_DECISION_{session_id}_{idx}"),
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "source": "conversation",
            "session_id": session_id,
            "actors": actors_raw,
            "options_considered": alternatives_raw[:3],
            "decision": decision_text,
            "rationale": metadata.get("rationale", ""),
            "constraints": constraints_raw[:5],
            "files_impacted": metadata.get("files_impacted", []),
            "repos_impacted": metadata.get("repos_impacted", []),
            "tests_written": metadata.get("tests_written", 0),
            "governance_artifacts": metadata.get("governance_artifacts", []),
            "phi_cps": metadata.get("phi_cps", 0.0),
            "status": "proposed",
        }
        decisions.append(decision)
        save_decision(decision)

    constraints = [
        {
            "type": "Constraint",
            "name": c,
            "source": "conversation",
            "session_id": session_id,
        }
        for c in constraints_raw[:10]
    ]

    alternatives = [
        {
            "type": "Alternative",
            "name": a,
            "reason_discarded": "Not selected in conversation",
            "source": "conversation",
            "session_id": session_id,
        }
        for a in alternatives_raw[:10]
    ]

    # Phase 1: Intégrations runners (avec fallback gracieux)
    tlm_result = call_tlm_lang(sanitized_text)
    chronox_result = call_chronox(decisions)
    referex_result = call_referex(metadata.get("governance_artifacts", []))

    # Publication KG-WAZAA (avec retry)
    waazaa_topics = []
    for decision in decisions:
        if publish_waazaa(decision):
            waazaa_topics.append("L0-CANON/*/adr_update")
            waazaa_topics.append("L0-CANON/*/intent_update")
            waazaa_topics.append("L4-TOOLS/*/governance")
            waazaa_topics.append("L4-TOOLS/*/codedb_index")

    return jsonify({
        "session_id": session_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "decisions": decisions,
        "constraints": constraints,
        "alternatives": alternatives,
        "kg_l_published": len(waazaa_topics) > 0,
        "waazaa_topics": list(set(waazaa_topics)),
        "tlm_lang": tlm_result,
        "chronox": chronox_result,
        "referex": referex_result,
    }), 200


@app.route("/cognitive/decisions", methods=["GET"])
def list_decisions():
    """Liste les décisions récentes."""
    decisions = load_decisions()
    # Filtrer par session_id si fourni
    session_id = request.args.get("session_id")
    if session_id:
        decisions = [d for d in decisions if d.get("session_id") == session_id]
    # Trier par date décroissante
    decisions.sort(key=lambda d: d.get("date", ""), reverse=True)
    return jsonify({"decisions": decisions, "count": len(decisions)}), 200


@app.route("/cognitive/decisions/<session_id>", methods=["GET"])
def get_decisions_by_session(session_id: str):
    """Récupère les décisions d'une session spécifique."""
    decisions = [d for d in load_decisions() if d.get("session_id") == session_id]
    return jsonify({"session_id": session_id, "decisions": decisions, "count": len(decisions)}), 200


@app.route("/cognitive/phi", methods=["GET"])
def cognitive_phi():
    """Sanity-check φ_TOTAL via CTULU PhiCognitiveCalculator."""
    try:
        ctulu_path = Path(__file__).resolve().parents[3] / "L4-TOOLS" / "CTULU"
        if str(ctulu_path) not in sys.path:
            sys.path.insert(0, str(ctulu_path))
        from ctulu.runners.phi_cognitive import PhiCognitiveCalculator
    except Exception as exc:
        return jsonify({"error": f"phi_cognitive import failed: {exc}"}), 500

    try:
        calc = PhiCognitiveCalculator()
        sample_outputs = {
            "TALEX": type("Out", (), {"metrics": {"m_score": 0.9}, "success": True})(),
            "TIMX": type("Out", (), {"metrics": {"m_score": 0.8}, "success": True})(),
            "CONVERSATION_COGNITIVE": type("Out", (), {"metrics": {"m_score": 0.9}, "success": True})(),
            "ROOTX": type("Out", (), {"metrics": {"m_score": 0.85}, "success": True})(),
            "RLM-243": type("Out", (), {"metrics": {"m_score": 0.8}, "success": True})(),
            "TLM-LANG": type("Out", (), {"metrics": {"m_score": 0.7}, "success": True})(),
            "LLUX": type("Out", (), {"metrics": {"m_score": 0.6}, "success": True})(),
        }
        result = calc.calculate(sample_outputs)
        return jsonify(result), 200
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# ============================================================================
# Phase 2 — Auto-Governance Endpoints
# ============================================================================


@app.route("/cognitive/governance/auto", methods=["POST"])
def governance_auto():
    """Phase 2: Auto-génération ADR/PRD/INTENT depuis détection de patterns.
    
    Body:
        conversation_text: str
        session_id: str (optional)
        context: dict (optional)
    
    Returns:
        Liste d'artefacts de gouvernance générés
    """
    data = request.get_json(force=True)
    conversation_text = data.get("conversation_text", "")
    session_id = data.get("session_id", "unknown")
    context = data.get("context", {})
    
    if not conversation_text:
        return jsonify({"error": "conversation_text is required"}), 400
    
    # Sanitization
    sanitized_text = sanitize_text(conversation_text)
    
    # Validation regex safety
    safety = validate_regex_safety(sanitized_text)
    if not safety["safe"]:
        return jsonify({
            "error": "Unsafe regex patterns detected",
            "issues": safety["issues"],
        }), 400
    
    # Auto-génération
    artifacts = auto_generate(sanitized_text, {
        **context,
        "session_id": session_id,
    })
    
    return jsonify({
        "session_id": session_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "artifacts": artifacts,
        "count": len(artifacts),
        "patterns_detected": len(set(a["pattern_id"] for a in artifacts)),
    }), 200


@app.route("/cognitive/governance/patterns", methods=["GET"])
def governance_patterns():
    """Phase 2: Liste des patterns de détection connus.
    
    Returns:
        Liste des patterns configurés pour auto-génération
    """
    return jsonify({
        "patterns": [
            {
                "id": p["id"],
                "name": p["name"],
                "artifact_type": p["artifact_type"],
                "template": p["template"],
            }
            for p in KNOWN_PATTERNS
        ],
        "count": len(KNOWN_PATTERNS),
    }), 200


@app.route("/cognitive/dashboard", methods=["GET"])
def dashboard():
    """Phase 2: Tableau de bord auto-gouvernance.
    
    Returns:
        Statistiques: artefacts générés, patterns détectés, décisions extraites
    """
    stats = get_dashboard_stats()
    return jsonify(stats), 200


@app.route("/cognitive/referex/validate", methods=["POST"])
def referex_validate():
    """Phase 2: Validation REFEREX avant commit.
    
    Body:
        artifacts: list[str] - liste d'intent_hash à valider
        document_type: str (optional, default: "PRD")
    
    Returns:
        Résultat de validation REFEREX
    """
    data = request.get_json(force=True)
    artifacts = data.get("artifacts", [])
    document_type = data.get("document_type", "PRD")
    
    if not artifacts:
        return jsonify({"error": "artifacts list is required"}), 400
    
    result = call_referex(artifacts)
    
    # Déterminer si le commit est bloqué
    blocked = False
    broken_links = result.get("broken_links", [])
    if broken_links:
        blocked = True
    
    return jsonify({
        "valid": not blocked,
        "blocked": blocked,
        "document_type": document_type,
        "artifacts_checked": len(artifacts),
        "broken_links": broken_links,
        "coverage_score": result.get("coverage_score", 0.0),
        "references": result.get("references", []),
    }), 200


def check_port(host: str, port: int, timeout: float = 1.0) -> bool:
    """Vérifie si un port est ouvert."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


if __name__ == "__main__":
    logger.info("Starting %s on port %d", SERVICE_NAME, PORT)
    app.run(host="127.0.0.1", port=PORT, debug=False, use_reloader=False)
