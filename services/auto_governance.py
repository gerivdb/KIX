"""Auto-Governance Engine for Conversation Cognitive Runner.

Phase 2 — Automatisation Governance
Détection de patterns connus → génération ADR/PRD/INTENT
Validation REFEREX avant commit
Notification KG-WAZAA vers GOVERNANCE-HUB
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("auto-governance")

# Répertoire de stockage des artefacts auto-générés
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "cognitive"
GOVERNANCE_DIR = DATA_DIR / "governance"
GOVERNANCE_DIR.mkdir(parents=True, exist_ok=True)

# Patterns connus → type de document à générer
KNOWN_PATTERNS = [
    {
        "id": "ADR_OPTION_SELECTION",
        "name": "Sélection d'option architecturale",
        "patterns": [
            r"(?:option\s+[A-Z]|choix\s+architecturale?|architecture\s+retenue?|retenu)[^:]*[:\-]\s*(.+)",
            r"(?:décision|decision)\s*[:\-]\s*(?:option\s+[A-Z]|architecture\s+.+)",
        ],
        "artifact_type": "ADR",
        "template": "adr_option_selection",
    },
    {
        "id": "PRD_FEATURE_REQUEST",
        "name": "Nouvelle fonctionnalité",
        "patterns": [
            r"(?:nouvelle?\s+fonctionnalité|feature\s+request|ajouter\s+un?\s+[^:]*)[^:]*[:\-]\s*(.+)",
            r"(?:besoin\s+de\s+|requête\s+de\s+|demande\s+de\s+)(.+)",
        ],
        "artifact_type": "PRD",
        "template": "prd_feature_request",
    },
    {
        "id": "INTENT_NEW_RUNNER",
        "name": "Nouveau runner cognitif",
        "patterns": [
            r"(?:nouveau\s+runner|créer\s+un?\s+runner)[^:]*[:\-]\s*(.+)",
            r"(?:runner\s+pour\s+[^:]*)[^:]*[:\-]\s*(.+)",
            r"(?:intent\s+de\s+|objectif\s+[:=]\s*)(.+)",
        ],
        "artifact_type": "INTENT",
        "template": "intent_new_runner",
    },
    {
        "id": "CONSTRAINT_BDCP",
        "name": "Contrainte BDCP",
        "patterns": [
            r"(?:BDCP\s+inviolable|BDCP\s+obligatoire|mode\s+BDCP)[^:]*[:\-]?\s*(.+)",
            r"(?:ne\s+pas\s+sortir\s+de\s+BDCP|interdiction\s+BDCP)[^:]*[:\-]?\s*(.+)",
        ],
        "artifact_type": "CONSTRAINT",
        "template": "constraint_bdcp",
    },
    {
        "id": "CONSTRAINT_KIVA",
        "name": "Contrainte KIVA-CLI",
        "patterns": [
            r"(?:KIVA-CLI\s+only|KIVA-CLI\s+obligatoire|uniquement\s+KIVA-CLI)[^:]*[:\-]?\s*(.+)",
            r"(?:interdiction\s+gh\s+|gh\s+interdit)[^:]*[:\-]?\s*(.+)",
        ],
        "artifact_type": "CONSTRAINT",
        "template": "constraint_kiva",
    },
]


def detect_patterns(text: str) -> list[dict[str, Any]]:
    """Détecte les patterns connus dans un texte."""
    detected = []
    for pattern_def in KNOWN_PATTERNS:
        for pattern in pattern_def["patterns"]:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                detected.append({
                    "pattern_id": pattern_def["id"],
                    "pattern_name": pattern_def["name"],
                    "artifact_type": pattern_def["artifact_type"],
                    "template": pattern_def["template"],
                    "matches": [m.strip() for m in matches if m.strip()],
                    "confidence": min(1.0, len(matches) * 0.3 + 0.5),
                })
                break
    return detected


def generate_adr_draft(pattern_match: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """Génère un draft ADR depuis un pattern matché."""
    intent_hash = context.get("intent_hash", f"0xADR_AUTO_{datetime.now().strftime('%Y%m%d%H%M%S')}")
    title = pattern_match["matches"][0] if pattern_match["matches"] else pattern_match["pattern_name"]
    
    return {
        "type": "ADR",
        "status": "proposed",
        "title": f"ADR — {title}",
        "intent_hash": intent_hash,
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "source": "auto_governance",
        "pattern_id": pattern_match["pattern_id"],
        "confidence": pattern_match["confidence"],
        "content": {
            "context": context.get("context", ""),
            "options_considered": context.get("options_considered", []),
            "decision": title,
            "rationale": context.get("rationale", "Auto-généré depuis détection de pattern"),
            "constraints": context.get("constraints", []),
            "consequences": context.get("consequences", "À documenter"),
        },
    }


def generate_prd_draft(pattern_match: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """Génère un draft PRD depuis un pattern matché."""
    intent_hash = context.get("intent_hash", f"0xPRD_AUTO_{datetime.now().strftime('%Y%m%d%H%M%S')}")
    title = pattern_match["matches"][0] if pattern_match["matches"] else pattern_match["pattern_name"]
    
    return {
        "type": "PRD",
        "status": "proposed",
        "title": f"PRD — {title}",
        "intent_hash": intent_hash,
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "source": "auto_governance",
        "pattern_id": pattern_match["pattern_id"],
        "confidence": pattern_match["confidence"],
        "content": {
            "problem": context.get("problem", "À définir"),
            "solution": context.get("solution", title),
            "scope": context.get("scope", {"includes": [], "excludes": []}),
            "acceptance_criteria": context.get("acceptance_criteria", []),
        },
    }


def generate_intent_draft(pattern_match: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """Génère un draft INTENT depuis un pattern matché."""
    intent_hash = context.get("intent_hash", f"0xINTENT_AUTO_{datetime.now().strftime('%Y%m%d%H%M%S')}")
    title = pattern_match["matches"][0] if pattern_match["matches"] else pattern_match["pattern_name"]
    
    return {
        "type": "INTENT",
        "status": "proposed",
        "title": f"INTENT — {title}",
        "intent_hash": intent_hash,
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "source": "auto_governance",
        "pattern_id": pattern_match["pattern_id"],
        "confidence": pattern_match["confidence"],
        "content": {
            "diagnostic": context.get("diagnostic", "À définir"),
            "solution": context.get("solution", title),
            "architecture": context.get("architecture", "À définir"),
            "success_criteria": context.get("success_criteria", []),
        },
    }


def generate_constraint_draft(pattern_match: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """Génère un draft de contrainte depuis un pattern matché."""
    intent_hash = context.get("intent_hash", f"0xCONSTRAINT_AUTO_{datetime.now().strftime('%Y%m%d%H%M%S')}")
    title = pattern_match["matches"][0] if pattern_match["matches"] else pattern_match["pattern_name"]
    
    return {
        "type": "CONSTRAINT",
        "status": "proposed",
        "title": f"Contrainte — {title}",
        "intent_hash": intent_hash,
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "source": "auto_governance",
        "pattern_id": pattern_match["pattern_id"],
        "confidence": pattern_match["confidence"],
        "content": {
            "name": title,
            "description": context.get("description", "Auto-généré depuis détection de pattern"),
            "scope": context.get("scope", "global"),
            "enforcement": context.get("enforcement", "governance"),
        },
    }


GENERATORS = {
    "ADR": generate_adr_draft,
    "PRD": generate_prd_draft,
    "INTENT": generate_intent_draft,
    "CONSTRAINT": generate_constraint_draft,
}


def auto_generate(text: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Pipeline auto-gouvernance : détection patterns → génération artefacts.
    
    Args:
        text: Texte de la conversation à analyser
        context: Contexte additionnel (actors, files_impacted, etc.)
    
    Returns:
        Liste d'artefacts de gouvernance générés
    """
    if context is None:
        context = {}
    
    patterns = detect_patterns(text)
    artifacts = []
    
    for pattern in patterns:
        generator = GENERATORS.get(pattern["artifact_type"])
        if generator:
            artifact = generator(pattern, context)
            artifacts.append(artifact)
            save_artifact(artifact)
            logger.info(
                "Auto-generated %s from pattern %s (confidence=%.2f)",
                pattern["artifact_type"],
                pattern["pattern_id"],
                pattern["confidence"],
            )
    
    return artifacts


def save_artifact(artifact: dict[str, Any]) -> None:
    """Sauvegarde un artefact auto-généré."""
    artifact_type = artifact.get("type", "UNKNOWN").lower()
    type_dir = GOVERNANCE_DIR / artifact_type
    type_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"{artifact.get('intent_hash', 'unknown')}.json"
    filepath = type_dir / filename
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(artifact, f, ensure_ascii=False, indent=2)


def load_artifacts(artifact_type: str | None = None) -> list[dict[str, Any]]:
    """Charge les artefacts auto-générés."""
    artifacts = []
    search_dir = GOVERNANCE_DIR / artifact_type if artifact_type else GOVERNANCE_DIR
    
    if not search_dir.exists():
        return artifacts
    
    for filepath in search_dir.glob("*.json"):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                artifacts.append(json.load(f))
        except (json.JSONDecodeError, OSError):
            continue
    
    return artifacts


def validate_regex_safety(text: str) -> dict[str, Any]:
    """Valide qu'un texte ne contient pas de patterns regex dangereux."""
    dangerous_patterns = [
        r"(?<!\\)\.\*\+",  # .*+ sans échappement
        r"\(\?[^\)]*\)",   # Groups non capturants mal formés
    ]
    issues = []
    for pattern in dangerous_patterns:
        if re.search(pattern, text):
            issues.append(f"Potentially dangerous regex pattern: {pattern}")
    
    return {
        "safe": len(issues) == 0,
        "issues": issues,
    }


def get_dashboard_stats() -> dict[str, Any]:
    """Statistiques pour le dashboard auto-gouvernance."""
    all_artifacts = load_artifacts()
    decisions = load_decisions() if "conversation_cognitive_runner" in globals() else []
    
    # Compter par type
    by_type: dict[str, int] = {}
    for artifact in all_artifacts:
        atype = artifact.get("type", "UNKNOWN")
        by_type[atype] = by_type.get(atype, 0) + 1
    
    # Pattern le plus détecté
    pattern_counts: dict[str, int] = {}
    for artifact in all_artifacts:
        pid = artifact.get("pattern_id", "unknown")
        pattern_counts[pid] = pattern_counts.get(pid, 0) + 1
    
    top_pattern = max(pattern_counts.items(), key=lambda x: x[1]) if pattern_counts else ("none", 0)
    
    return {
        "total_artifacts": len(all_artifacts),
        "by_type": by_type,
        "total_decisions": len(decisions),
        "top_pattern": top_pattern,
        "pattern_counts": pattern_counts,
        "last_generated": datetime.now(timezone.utc).isoformat(),
    }


def load_decisions() -> list[dict[str, Any]]:
    """Charge les décisions depuis le fichier local (import depuis conversation_cognitive_runner)."""
    try:
        decisions_file = DATA_DIR / "cognitive_decisions.json"
        if not decisions_file.exists():
            return []
        with open(decisions_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []
