---
owner: L2-PLATFORM

type: PRD-MOC
version: "1.0.0"
date: "2026-09-28"
status: approved
intent_hash: 0xPRD_MOC_KIX_META_DESIGN_SELF_HEALING_CONSUMER_20260928
citizen: "L2-KIX"
layer: "L2"
author: gerivdb
source_repo: gerivdb/KIX
source_path: PRD-MOC/PRD-MOC-KIX-META-DESIGN-SELF-HEALING-CONSUMER-20260928.md
pole_id: POLE-KG-TDC-001
---

# PRD MOC - KIX Meta-Design Self-Healing Consumer

> **Verdict** : PRD_MOC — Rendre obligatoire l'application du design `meta-design-self-healing` dans KIX.
> **Source** : Design `meta-design-self-healing` (`designs/meta-design-self-healing/design.yaml`), ADR-2026-09-21-008-META-DESIGN-SELF-HEALING, PRD-MOC-META-DESIGN-SELF-HEALING-20260921.
> **Constat** : KIX est consumer de `meta-design-self-healing` mais n'a pas de PRD-MOC local déclarant cette obligation.

---

## 1. Contexte

KIX est un consumer du design `meta-design-self-healing`. Toute opération KIX DOIT détecter les gaps structurels et proposer des patches atomiques.

---

## 2. Problème

| Symptôme | Cause racine | Impact |
|----------|--------------|--------|
| Gaps structurels non détectés | Pas de self-healing | Dérive architecturale |
| Doublons d'ID | Pas de détection | Conflits de nommage |

---

## 3. Objectif

Intégrer le mécanisme d'auto-guérison dans toutes les opérations KIX.

---

## 4. Périmètre

### 4.1 In Scope

| Opération | Application |
|-----------|-------------|
| Déploiement | Self-healing avant déploiement |
| Configuration | Self-healing avant modification |
| Orchestration | Self-healing avant orchestration |

### 4.2 Out of Scope

- Modification du design `meta-design-self-healing` lui-même
- Application automatique des patches

---

## 5. Architecture

### 5.1 Intégration KIX

```python
# kix/pipelines/meta_design_self_healing.py
from meta_design_self_healing import MetaDesignSelfHealing

class MetaDesignSelfHealingKix:
    def scan(self, context):
        healing = MetaDesignSelfHealing()
        return healing.scan(context)
```

---

## 6. Livrables

| ID | Livrable | Chemin cible | Type |
|---|---|---|---|
| L1 | PRD-MOC `meta-design-self-healing` | `PRD-MOC/PRD-MOC-KIX-META-DESIGN-SELF-HEALING-CONSUMER-20260928.md` | Créer |
| L2 | Script KIX | `kix/pipelines/meta_design_self_healing.py` | Créer |
| L3 | Tests unitaires | `tests/test_meta_design_self_healing_kix.py` | Créer |

---

## 7. Critères d'acceptation

1. `meta_design_self_healing.py` intègre le self-healing.
2. Tests unitaires passent.
3. Proof-of-Life horodatée dans ce PRD-MOC.

---

## 8. Références

- **Design** : `designs/meta-design-self-healing/design.yaml`
- **ADR** : ADR-2026-09-21-008-META-DESIGN-SELF-HEALING
- **PRD-MOC** : PRD-MOC-META-DESIGN-SELF-HEALING-20260921
- **Meta-design** : `meta-design.yaml` (design meta-design-self-healing)

---

## 9. Proof-of-Life

- [x] 2026-09-28T03:13:33+02:00 — Création de ce PRD-MOC.
- [ ] 2026-09-28T03:13:33+02:00 — Script KIX créé et testé.
- [ ] 2026-09-28T03:13:33+02:00 — Tests unitaires passent.
