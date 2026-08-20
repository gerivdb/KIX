---
type: DOC
version: "1.0.0"
intent_hash: 0xDOC_COGNITIVE_DECISIONS_API_20260821
date: "2026-08-21"
---

# API Documentation — Cognitive Decisions

## Base URL

```
http://127.0.0.1:8811
```

## Endpoints

### 1. Health Check

**`GET /cognitive/conversation/health`**

Vérifie que le runner est opérationnel.

**Réponse 200** :
```json
{
  "status": "ok",
  "service": "conversation-cognitive",
  "port": 8811
}
```

### 2. Analyser une conversation

**`POST /cognitive/conversation/analyze`**

Extrait les décisions, contraintes et alternatives depuis une conversation.

**Corps de la requête** :
```json
{
  "conversation_text": "Décision : Option B choisie pour le bootstrap runner.",
  "session_id": "kix-bootstrap-001",
  "actors": ["user", "kilo"],
  "metadata": {
    "intent_hash": "0xBOOTSTRAP_RUNNER_OPTION_B_20260820",
    "rationale": "Séparation des responsabilités",
    "files_impacted": ["KIX/config/runners.yaml"],
    "repos_impacted": ["KIX", "GOVERNANCE-HUB"],
    "tests_written": 21,
    "governance_artifacts": ["ADR-2026-08-20-001"],
    "phi_cps": 0.375
  }
}
```

**Réponse 200** :
```json
{
  "session_id": "kix-bootstrap-001",
  "timestamp": "2026-08-21T00:30:00Z",
  "decisions": [
    {
      "type": "Decision",
      "intent_hash": "0xBOOTSTRAP_RUNNER_OPTION_B_20260820",
      "date": "2026-08-21",
      "source": "conversation",
      "session_id": "kix-bootstrap-001",
      "actors": ["user", "kilo"],
      "options_considered": ["option_a_inline", "option_b_separate_runner"],
      "decision": "Option B choisie",
      "rationale": "Séparation des responsabilités",
      "constraints": ["BDCP inviolable", "KIVA-CLI only"],
      "files_impacted": ["KIX/config/runners.yaml"],
      "repos_impacted": ["KIX", "GOVERNANCE-HUB"],
      "tests_written": 21,
      "governance_artifacts": ["ADR-2026-08-20-001"],
      "phi_cps": 0.375,
      "status": "proposed"
    }
  ],
  "constraints": [
    {
      "type": "Constraint",
      "name": "BDCP inviolable",
      "source": "conversation",
      "session_id": "kix-bootstrap-001"
    }
  ],
  "alternatives": [
    {
      "type": "Alternative",
      "name": "option_a_inline",
      "reason_discarded": "Overloading gateway-manager",
      "source": "conversation",
      "session_id": "kix-bootstrap-001"
    }
  ],
  "kg_l_published": true,
  "waazaa_topics": [
    "L0-CANON/*/adr_update",
    "L0-CANON/*/intent_update",
    "L4-TOOLS/*/governance",
    "L4-TOOLS/*/codedb_index"
  ],
  "tlm_lang": {"ambiguities": [], "score": 0.0},
  "chronox": {"timeline": []},
  "referex": {"valid": true, "broken_links": []}
}
```

**Réponse 400** :
```json
{
  "error": "conversation_text is required"
}
```

### 3. Lister les décisions

**`GET /cognitive/decisions`**

Retourne les décisions récentes, triées par date décroissante.

**Paramètres** :
- `session_id` (optionnel) — filtrer par session

**Réponse 200** :
```json
{
  "decisions": [...],
  "count": 42
}
```

### 4. Décisions d'une session

**`GET /cognitive/decisions/{session_id}`**

Retourne les décisions d'une session spécifique.

**Réponse 200** :
```json
{
  "session_id": "kix-bootstrap-001",
  "decisions": [...],
  "count": 3
}
```

## Codes d'erreur

| Code | Signification |
|------|---------------|
| 200 | Succès |
| 400 | Requête invalide (champ manquant) |
| 500 | Erreur serveur |

## Limites

- Max 5 décisions par appel `analyze`
- Max 1000 décisions stockées localement (FIFO)
- Timeout intégré : 2s par défaut pour les appels runners externes

## Sécurité

Tout secret/token détecté dans `conversation_text` est remplacé par `[REDACTED]`
avant traitement et publication.

## Références

- **PRD** : `PRD-MOC-COGNITIVE-CONVERSATION-RUNNER-KG-L-WAZAA-2026-08-21.md`
- **ADR** : `ADR-2026-08-21-conversation-cognitive-runner.md`
- **Schéma** : `schemas/runners/cognitive-conversation-decision.schema.json`
