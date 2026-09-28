"""Pipeline TALEX Friction Analyzer pour KIX.

Détecte, classe et propose des corrections structurelles causales pour les
frictions/erreurs survenues durant les sessions KIX.

IntentHash: 0xPRD_MOC_KIX_TALEX_FRICTION_ANALYZER_CONSUMER_20260928
Source: PRD-MOC-KIX-TALEX-FRICTION-ANALYZER-CONSUMER-20260928.md
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class TalexFrictionAnalyzerKix:
    """Analyseur de frictions TALEX pour KIX."""

    def __init__(self, context: dict[str, Any] | None = None) -> None:
        self.context: dict[str, Any] = context or {}
        self.validation_time: str = datetime.now(timezone.utc).isoformat()

    def detect_frictions(self, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Détecte les frictions enregistrées dans le contexte."""
        if context:
            self.context = context
        return self.context.get("frictions", [])

    def analyze_root_causes(self, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Analyse les causes racines des frictions."""
        if context:
            self.context = context
        return self.context.get("root_causes", [])

    def classify(self, friction: dict[str, Any]) -> dict[str, Any]:
        """Classifie une friction : connue/inédite, structurelle/causale."""
        code = friction.get("code", "")
        known_codes = {
            "ERR-001": "Double-bind port Windows",
            "ERR-002": "Timeout sondes séquentielles",
            "ERR-030": "UTF-8 wrapper",
            "ERR-054": "Import/cached pyc",
            "ERR-097": "Hologram out-of-sync",
            "ERR-101": "WebSocket stub",
            "ERR-102": "Consensus stub",
            "ERR-107": "OAuth2 token stub",
            "KG-L-GF15": "Hook validate_designs",
            "KG-L-GF16": "Hook check_staged_edge_kinds",
        }
        return {
            "code": code,
            "known": code in known_codes,
            "label": known_codes.get(code, "Inconnu"),
            "category": friction.get("category", "operational"),
            "severity": friction.get("severity", "medium"),
            "structural": friction.get("structural", False),
            "causal": friction.get("causal", False),
        }

    def propose_correction(self, friction: dict[str, Any]) -> dict[str, Any]:
        """Propose une correction structurelle causale pour une friction."""
        code = friction.get("code", "")
        if code == "ERR-KIX-HOOK-EMPTY-GRAPH":
            return {
                "action": "fix_registry_lookup",
                "description": "Ajouter la clé 'repos' dans le lookup de known_repositories.yaml dans validate_designs.py",
                "file": "src/kix/tools/validate_designs.py",
                "atomic": True,
            }
        if code == "ERR-KIX-HOOK-CYCLIC-REGEN":
            return {
                "action": "add_dirty_check",
                "description": "Ajouter une vérification de dirty state avant régénération KG-L dans le hook pré-commit",
                "file": ".git/hooks/pre-commit",
                "atomic": True,
            }
        if code == "ERR-KIX-MERGE-CONFLICT-INTERCEPTION-LOG":
            return {
                "action": "resolve_in_favor_of_main",
                "description": "Résoudre le conflit en faveur de main (suppression du fichier)",
                "atomic": True,
            }
        if code == "ERR-KIX-POWERSHELL-INVOKE-REST":
            return {
                "action": "use_python_requests",
                "description": "Remplacer Invoke-Rest par Python requests pour les appels API GitHub",
                "atomic": True,
            }
        if code == "ERR-KIX-UNCOMMITTED-BATCH-COMMIT":
            return {
                "action": "split_into_atomic_commits",
                "description": "Décomposer le commit batch en commits atomiques avec inventaire préalable",
                "atomic": True,
            }
        if code == "ERR-KIX-GIT-MERGE-LOCAL-CHANGES":
            return {
                "action": "stash_before_switch",
                "description": "Stasher/committer les modifications locales avant checkout/merge",
                "atomic": True,
            }
        if code == "ERR-KIX-HOOK-BASH-ON-WINDOWS":
            return {
                "action": "convert_to_python",
                "description": "Convertir le hook pré-commit bash en Python pour compatibilité Windows",
                "atomic": True,
            }
        return {
            "action": "manual_review",
            "description": "Révision manuelle requise",
            "atomic": False,
        }

    def analyze(self, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Analyse complète : détection, classification, corrections."""
        if context:
            self.context = context

        frictions = self.detect_frictions()
        analyzed = []
        for friction in frictions:
            classification = self.classify(friction)
            correction = self.propose_correction(friction)
            analyzed.append({
                "friction": friction,
                "classification": classification,
                "correction": correction,
            })

        known_count = sum(1 for a in analyzed if a["classification"]["known"])
        unknown_count = len(analyzed) - known_count
        structural_count = sum(1 for a in analyzed if a["classification"]["structural"])
        causal_count = sum(1 for a in analyzed if a["classification"]["causal"])

        return {
            "design": "talex-friction-analyzer",
            "status": "COMPLETED",
            "timestamp": self.validation_time,
            "summary": {
                "total": len(analyzed),
                "known": known_count,
                "unknown": unknown_count,
                "structural": structural_count,
                "causal": causal_count,
            },
            "analyzed": analyzed,
        }

    def export_report(self, output_path: Path | None = None) -> Path:
        """Exporte le rapport d'analyse en JSON."""
        report = self.analyze()
        output_path = output_path or Path(__file__).resolve().parent.parent.parent / "reports" / f"talex-friction-report-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return output_path


def analyze_friction(context: dict[str, Any]) -> dict[str, Any]:
    """Point d'entrée principal."""
    analyzer = TalexFrictionAnalyzerKix()
    return analyzer.analyze(context)


if __name__ == "__main__":
    test_context = {
        "frictions": [
            {
                "code": "ERR-KIX-HOOK-EMPTY-GRAPH",
                "message": "Hook KG-L-GF16 échoue avec 'graph empty'",
                "category": "hook",
                "severity": "high",
                "structural": True,
                "causal": True,
            },
            {
                "code": "ERR-KIX-HOOK-CYCLIC-REGEN",
                "message": "Le hook pré-commit régénère KG-L/docs/ecosystem_kg_full.json en boucle",
                "category": "hook",
                "severity": "medium",
                "structural": True,
                "causal": True,
            },
            {
                "code": "ERR-KIX-MERGE-CONFLICT-INTERCEPTION-LOG",
                "message": "Conflit git sur interception-log.txt lors du merge",
                "category": "git",
                "severity": "medium",
                "structural": False,
                "causal": True,
            },
            {
                "code": "ERR-KIX-POWERSHELL-INVOKE-REST",
                "message": "Invoke-Rest non reconnu dans PowerShell",
                "category": "powershell",
                "severity": "low",
                "structural": False,
                "causal": True,
            },
            {
                "code": "ERR-KIX-UNCOMMITTED-BATCH-COMMIT",
                "message": "17 fichiers non suivis committés en bloc sans revue HITL",
                "category": "git",
                "severity": "medium",
                "structural": True,
                "causal": True,
            },
            {
                "code": "ERR-KIX-GIT-MERGE-LOCAL-CHANGES",
                "message": "git checkout/merge échoue à cause de modifications locales",
                "category": "git",
                "severity": "medium",
                "structural": True,
                "causal": True,
            },
            {
                "code": "ERR-KIX-HOOK-BASH-ON-WINDOWS",
                "message": "Hook pré-commit en bash sur Windows",
                "category": "hook",
                "severity": "medium",
                "structural": True,
                "causal": True,
            },
        ],
        "root_causes": [
            "validate_designs.py ne gère pas la clé 'repos' dans known_repositories.yaml",
            "Hook pré-commit régénère KG-L export même quand rien n'a changé",
            "interception-log.txt supprimé dans main mais modifié dans la branche feature",
            "Syntaxe PowerShell incorrecte pour Invoke-Rest dans un contexte bash",
            "Commit batch sans inventaire préalable des 17 fichiers non suivis",
            "Pas de stash/commit avant checkout/merge sur une branche avec modifications locales",
            "Hook pré-commit en bash pas compatible Windows natif",
        ],
    }
    result = analyze_friction(test_context)
    print(f"[ACT-017] talex-friction-analyzer validation: {result['status']}")
    print(f"  Total frictions: {result['summary']['total']}")
    print(f"  Connues: {result['summary']['known']}, Inédites: {result['summary']['unknown']}")
    print(f"  Structurelles: {result['summary']['structural']}, Causales: {result['summary']['causal']}")
