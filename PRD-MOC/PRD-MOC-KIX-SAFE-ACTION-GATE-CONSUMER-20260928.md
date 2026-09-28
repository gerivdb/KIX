---
owner: L2-PLATFORM

type: PRD-MOC
version: "1.0.0"
date: "2026-09-28"
status: approved
intent_hash: 0xPRD_MOC_KIX_SAFE_ACTION_GATE_CONSUMER_20260928
citizen: "L2-KIX"
layer: "L2"
author: gerivdb
source_repo: gerivdb/KIX
source_path: PRD-MOC/PRD-MOC-KIX-SAFE-ACTION-GATE-CONSUMER-20260928.md
pole_id: POLE-KG-TDC-001
---

# PRD MOC - KIX Safe-Action Gate Consumer

> **Verdict** : PRD_MOC — Rendre obligatoire l'application du design `safe-action-gate` dans KIX.
> **Source** : Design `safe-action-gate` (`designs/safe-action-gate/design.yaml`), ADR-2026-09-21-005-SAFE-ACTION-GATE, PRD-MOC-SAFE-ACTION-GATE-20260921.
> **Constat** : KIX est consumer de `safe-action-gate` mais n'a pas de PRD-MOC local déclarant cette obligation.

---

## 1. Contexte

KIX est un consumer du design `safe-action-gate`. Toute opération KIX qui effectue une mutation DOIT passer par le gate avant d'être autorisée.

---

## 2. Problème

| Symptôme | Cause racine | Impact |
|----------|--------------|--------|
| Opérations sans préconditions | Pas de safe-action-gate appliqué | Actions risquées |
| Pas de preuve horodatée | Pas d'invariant respecté | Traçabilité absente |

---

## 3. Objectif

Intégrer le safe-action gate dans toutes les opérations KIX qui effectuent des mutations.

---

## 4. Périmètre

### 4.1 In Scope

| Opération | Application |
|-----------|-------------|
| Déploiement | Gate avant déploiement |
| Configuration | Gate avant modification |
| Orchestration | Gate avant orchestration |

### 4.2 Out of Scope

- Modification du design `safe-action-gate` lui-même
- Opérations en lecture seule

---

## 5. Architecture

### 5.1 Intégration KIX

```python
# kix/pipelines/safe_action_gate.py
from safe_action_gate import SafeActionGate

class SafeActionGateKix:
    def verify(self, context):
        gate = SafeActionGate()
        return gate.verify(context)
```

---

## 6. Livrables

| ID | Livrable | Chemin cible | Type |
|---|---|---|---|
| L1 | PRD-MOC `safe-action-gate` | `PRD-MOC/PRD-MOC-KIX-SAFE-ACTION-GATE-CONSUMER-20260928.md` | Créer |
| L2 | Script KIX | `kix/pipelines/safe_action_gate.py` | Créer |
| L3 | Tests unitaires | `tests/test_safe_action_gate_kix.py` | Créer |

---

## 7. Critères d'acceptation

1. `safe_action_gate.py` intègre le safe-action gate.
2. Tests unitaires passent.
3. Proof-of-Life horodatée dans ce PRD-MOC.

---

## 8. Références

- **Design** : `designs/safe-action-gate/design.yaml`
- **ADR** : ADR-2026-09-21-005-SAFE-ACTION-GATE
- **PRD-MOC** : PRD-MOC-SAFE-ACTION-GATE-20260921
- **Meta-design** : `meta-design.yaml` (design safe-action-gate)

---

## 9. Proof-of-Life

- [x] 2026-09-28T03:13:33+02:00 — Création de ce PRD-MOC.
- [ ] 2026-09-28T03:13:33+02:00 — Script KIX créé et testé.
- [ ] 2026-09-28T03:13:33+02:00 — Tests unitaires passent.
