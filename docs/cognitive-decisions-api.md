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

### 5. Sanity-check φ_TOTAL

**`GET /cognitive/phi`**

Calcule φ_TOTAL via `PhiCognitiveCalculator` avec des scores sample.

**Réponse 200** :
```json
{
  "global_score": 0.8326,
  "per_runner": {
    "TALEX": {"m_score": 0.9, "w_score": 0.2174, "weighted_contribution": 0.1957},
    "TIMX": {"m_score": 0.8, "w_score": 0.1304, "weighted_contribution": 0.1043},
    "CONVERSATION_COGNITIVE": {"m_score": 0.9, "w_score": 0.1739, "weighted_contribution": 0.1565},
    "ROOTX": {"m_score": 0.85, "w_score": 0.2174, "weighted_contribution": 0.1848},
    "RLM-243": {"m_score": 0.8, "w_score": 0.1304, "weighted_contribution": 0.1043},
    "TLM-LANG": {"m_score": 0.7, "w_score": 0.0870, "weighted_contribution": 0.0609},
    "LLUX": {"m_score": 0.6, "w_score": 0.0435, "weighted_contribution": 0.0261}
  },
  "weights": {
    "TALEX": 0.2174,
    "TIMX": 0.1304,
    "CONVERSATION_COGNITIVE": 0.1739,
    "ROOTX": 0.2174,
    "RLM-243": 0.1304,
    "TLM-LANG": 0.0870,
    "LLUX": 0.0435
  },
  "threshold": 0.8,
  "verdict": "A_VALIDER",
  "target": 0.85,
  "calculation_details": {
    "numerator": 0.8326,
    "denominator": 1.0,
    "calculation_steps": [
      "phi = sum(w_i * m_i) / sum(w_i)",
      "  TALEX: 0.2174 * 0.9 = 0.1957",
      "  TIMX: 0.1304 * 0.8 = 0.1043",
      "  CONVERSATION_COGNITIVE: 0.1739 * 0.9 = 0.1565",
      "  ROOTX: 0.2174 * 0.85 = 0.1848",
      "  RLM-243: 0.1304 * 0.8 = 0.1043",
      "  TLM-LANG: 0.0870 * 0.7 = 0.0609",
      "  LLUX: 0.0435 * 0.6 = 0.0261",
      "  phi = 0.8326 / 1.0 = 0.8326"
    ]
  }
}
```

**Codes d'erreur** :
- `500` : `phi_cognitive` import failed

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
