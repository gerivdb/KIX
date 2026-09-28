---
owner: L2-PLATFORM

type: PRD-MOC
version: "1.0.0"
date: "2026-09-28"
status: approved
intent_hash: 0xPRD_MOC_KIX_SAFE_ACTION_PATTERN_CONSUMER_20260928
citizen: "L2-KIX"
layer: "L2"
author: gerivdb
source_repo: gerivdb/KIX
source_path: PRD-MOC/PRD-MOC-KIX-SAFE-ACTION-PATTERN-CONSUMER-20260928.md
pole_id: POLE-KG-TDC-001
---

# PRD MOC - KIX Safe-Action Pattern Consumer

> **Verdict** : PRD_MOC — Rendre obligatoire l'application du design `safe-action-pattern` dans KIX.
> **Source** : Design `safe-action-pattern` (`designs/safe-action-pattern.yaml`), ADR-2026-09-19-SAFE-ACTION-PATTERN, PRD-MOC-SAFE-ACTION-PATTERN-20260919.
> **Constat** : KIX est consumer de `safe-action-pattern` mais n'a pas de PRD-MOC local déclarant cette obligation.

---

## 1. Contexte

KIX est un consumer du design `safe-action-pattern`. Toute opération KIX qui effectue une mutation (déploiement, configuration, orchestration) DOIT passer par le PATRON-0.

---

## 2. Problème

| Symptôme | Cause racine | Impact |
|----------|--------------|--------|
| Opérations sans préconditions | Pas de safe-action appliqué | Actions risquées |
| Pas de preuve horodatée | Pas d'invariant respecté | Traçabilité absente |

---

## 3. Objectif

Intégrer le PATRON-0 dans toutes les opérations KIX qui effectuent des mutations.

---

## 4. Périmètre

### 4.1 In Scope

| Opération | Application |
|-----------|-------------|
| Déploiement | Safe-action gate avant déploiement |
| Configuration | Safe-action gate avant modification |
| Orchestration | Safe-action gate avant orchestration |

### 4.2 Out of Scope

- Modification du design `safe-action-pattern` lui-même
- Opérations en lecture seule

---

## 5. Architecture

### 5.1 Intégration KIX

```python
# kix/pipelines/safe_action_gate.py
from safe_action_pattern import SafeActionGate

class SafeActionKix:
    def execute(self, context):
        gate = SafeActionGate()
        if not gate.validate(context):
            raise KixError("Safe-action gate failed")
        # ... execution logic
```

---

## 6. Livrables

| ID | Livrable | Chemin cible | Type |
|---|---|---|---|
| L1 | PRD-MOC `safe-action-pattern` | `PRD-MOC/PRD-MOC-KIX-SAFE-ACTION-PATTERN-CONSUMER-20260928.md` | Créer |
| L2 | Script KIX | `kix/pipelines/safe_action_gate.py` | Créer |
| L3 | Tests unitaires | `tests/test_safe_action_kix.py` | Créer |

---

## 7. Critères d'acceptation

1. `safe_action_gate.py` intègre le safe-action gate.
2. Tests unitaires passent.
3. Proof-of-Life horodatée dans ce PRD-MOC.

---

## 8. Références

- **Design** : `designs/safe-action-pattern.yaml`
- **ADR** : ADR-2026-09-19-SAFE-ACTION-PATTERN
- **PRD-MOC** : PRD-MOC-SAFE-ACTION-PATTERN-20260919
- **Meta-design** : `meta-design.yaml` (design safe-action-pattern)

---

## 9. Proof-of-Life

- [x] 2026-09-28T03:13:33+02:00 — Création de ce PRD-MOC.
- [ ] 2026-09-28T03:13:33+02:00 — Script KIX créé et testé.
- [ ] 2026-09-28T03:13:33+02:00 — Tests unitaires passent.
