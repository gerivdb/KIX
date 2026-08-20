---
type: DOC
version: "1.0.0"
intent_hash: 0xDOC_COGNITIVE_CONVERSATION_RUNNER_20260821
date: "2026-08-21"
---

# Cognitive Conversation Runner — Documentation Technique

## Vue d'ensemble

Le `conversation-cognitive` est un runner cognitif KIX dédié à l'extraction,
la structuration et la publication des décisions architecturales depuis les
conversations KiloCode vers **KG-L** et **KG-WAZAA**.

**Port** : 8811  
**Type** : Python (Flask)  
**Strate** : L2-PLATFORM  
**Working dir** : `D:/DO/WEB/TOOLS/L2-PLATFORM/KIX`  
**Entrypoint** : `services/conversation_cognitive_runner.py`

## Architecture interne

```
conversation-cognitive (port 8811)
├── /cognitive/conversation/health
│   └── GET → 200 if running
├── /cognitive/conversation/analyze
│   └── POST → JSON with extracted decisions
├── /cognitive/decisions
│   └── GET → List of recent decisions
├── /cognitive/decisions/{session_id}
│   └── GET → Decisions for specific session
├── TlmLangClient (amont, Phase 1)
├── DecisionExtractor (core)
├── ChronoxClient (aval, Phase 1)
├── ReferexClient (aval, Phase 1)
├── WazaaPublisher (aval, Phase 1)
├── KGLocalStorage
│   └── cognitive_decisions.json
└── Sanitizer
    └── Filtrage secrets/PII
```

## Pipeline de traitement

```
Conversation KiloCode
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  conversation-cognitive (port 8811)                             │
│                                                                 │
│  1. TLM-LANG (amont, Phase 1)                                  │
│     → Détection ambiguïtés sémantiques                          │
│                                                                 │
│  2. Extraction                                                  │
│     → Patterns : "décision", "option", "choix", "arbitrage"   │
│     → Entités : Decision, Actor, Constraint, Alternative       │
│                                                                 │
│  3. CHRONOX (aval, Phase 1)                                    │
│     → Timeline des décisions                                    │
│                                                                 │
│  4. REFEREX (aval, Phase 1)                                    │
│     → Validation cohérence ADR/PRD/INTENT                      │
│                                                                 │
│  5. Publication                                                 │
│     → KG-WAZAA topics                                          │
│     → cognitive_decisions.json (local)                         │
└─────────────────────────────────────────────────────────────────┘
```

## Entités KG-L

### Decision

```json
{
  "type": "Decision",
  "intent_hash": "0x...",
  "date": "2026-08-21",
  "source": "conversation",
  "session_id": "kix-bootstrap-001",
  "actors": ["user", "kilo"],
  "options_considered": ["option_a", "option_b"],
  "decision": "Option B choisie",
  "rationale": "...",
  "constraints": ["BDCP inviolable"],
  "files_impacted": ["KIX/config/runners.yaml"],
  "repos_impacted": ["KIX", "GOVERNANCE-HUB"],
  "tests_written": 21,
  "governance_artifacts": ["ADR-..."],
  "phi_cps": 0.375,
  "status": "proposed"
}
```

### Actor

```json
{
  "type": "Actor",
  "name": "user",
  "source": "conversation",
  "session_id": "test-001"
}
```

### Constraint

```json
{
  "type": "Constraint",
  "name": "BDCP inviolable",
  "source": "conversation",
  "session_id": "test-001"
}
```

### Alternative

```json
{
  "type": "Alternative",
  "name": "option_a_inline",
  "reason_discarded": "Overloading gateway-manager",
  "source": "conversation",
  "session_id": "test-001"
}
```

## Sécurité

Le runner implémente un **filtrage systématique** avant publication :

```python
SENSITIVE_PATTERNS = [
    r"Bearer\s+[A-Za-z0-9_\-]+",
    r"password\s*[:=]\s*['\"]?[A-Za-z0-9_\-]+",
    r"token\s*[:=]\s*['\"]?[A-Za-z0-9_\-]+",
    r"secret\s*[:=]\s*['\"]?[A-Za-z0-9_\-]+",
    r"gh[ps]_[A-Za-z0-9_]{4,}",
    r"sk-[A-Za-z0-9]{4,}",
]
```

Tout secret détecté est remplacé par `[REDACTED]`.

## Performance

| Opération | Cible |
|-----------|-------|
| `/cognitive/conversation/health` | < 50ms |
| `/cognitive/conversation/analyze` | < 2s |
| Publication KG-WAZAA | < 500ms |
| Extraction TLM-LANG | < 500ms |
| Validation REFEREX | < 1s |

**Budget RAM ENV2** : ~200-300 Mo par instance. Max 1 instance.

## Intégration CTULU Fusion

Le runner est intégré dans `MultiRunnerFusion` via `PhiCognitiveCalculator` :

```python
DEFAULT_WEIGHTS = {
    "TALEX": 0.25,
    "TIMX": 0.15,
    "CONVERSATION-COGNITIVE": 0.20,  # NOUVEAU
    "ROOTX": 0.25,
    "RLM-243": 0.15,
    "TLM-LANG": 0.10,
    "LLUX": 0.05,
}
# TOTAL = 1.00
```

## Références

- **PRD** : `PRD-MOC-COGNITIVE-CONVERSATION-RUNNER-KG-L-WAZAA-2026-08-21.md`
- **INTENT** : `INTENT-COGNITIVE-CONVERSATION-RUNNER-KG-L-WAZAA-2026-08-21.md`
- **ADR** : `ADR-2026-08-21-conversation-cognitive-runner.md`
- **Schéma** : `schemas/runners/cognitive-conversation-decision.schema.json`
