---
owner: L2-PLATFORM

type: PRD-MOC
version: "1.0.0"
date: "2026-09-28"
status: approved
intent_hash: 0xPRD_MOC_KIX_TALEX_FRICTION_ANALYZER_CONSUMER_20260928
citizen: "L2-KIX"
layer: "L2"
author: gerivdb
source_repo: gerivdb/KIX
source_path: PRD-MOC/PRD-MOC-KIX-TALEX-FRICTION-ANALYZER-CONSUMER-20260928.md
pole_id: POLE-KG-TDC-001
---

# PRD MOC - KIX Talex Friction Analyzer Consumer

> **Verdict** : PRD_MOC — Rendre obligatoire l'application du design `talex-friction-analyzer` dans KIX.
> **Source** : Design `talex-friction-analyzer` (`designs/talex-friction-analyzer/design.yaml`), PRD-MOC-TALEX-FRICTION-ANALYZER-20260922.
> **Constat** : KIX est consumer de `talex-friction-analyzer` mais n'a pas de PRD-MOC local déclarant cette obligation.

---

## 1. Contexte

KIX est un consumer du design `talex-friction-analyzer`. Toute opération KIX DOIT détecter et analyser les frictions de manière causale.

---

## 2. Problème

| Symptôme | Cause racine | Impact |
|----------|--------------|--------|
| Frictions non détectées | Design non appliqué | Erreurs répétées |
| Pas d'analyse causale | Design non appliqué | Dette technique |

---

## 3. Objectif

Intégrer l'analyse des frictions TALEX dans toutes les opérations KIX.

---

## 4. Périmètre

### 4.1 In Scope

| Opération | Application |
|-----------|-------------|
| Déploiement | Friction analyzer avant déploiement |
| Configuration | Friction analyzer avant modification |
| Orchestration | Friction analyzer avant orchestration |

### 4.2 Out of Scope

- Modification du design `talex-friction-analyzer` lui-même
- Opérations en lecture seule

---

## 5. Architecture

### 5.1 Intégration KIX

```python
# kix/pipelines/talex_friction_analyzer.py
from talex_friction_analyzer import TalexFrictionAnalyzer

class TalexFrictionAnalyzerKix:
    def analyze(self, context):
        analyzer = TalexFrictionAnalyzer()
        return analyzer.analyze(context)
```

---

## 6. Livrables

| ID | Livrable | Chemin cible | Type |
|---|---|---|---|
| L1 | PRD-MOC `talex-friction-analyzer` | `PRD-MOC/PRD-MOC-KIX-TALEX-FRICTION-ANALYZER-CONSUMER-20260928.md` | Créer |
| L2 | Script KIX | `kix/pipelines/talex_friction_analyzer.py` | Créer |
| L3 | Tests unitaires | `tests/test_talex_friction_analyzer_kix.py` | Créer |

---

## 7. Critères d'acceptation

1. `talex_friction_analyzer.py` intègre l'analyse des frictions.
2. Tests unitaires passent.
3. Proof-of-Life horodatée dans ce PRD-MOC.

---

## 8. Références

- **Design** : `designs/talex-friction-analyzer/design.yaml`
- **PRD-MOC** : PRD-MOC-TALEX-FRICTION-ANALYZER-20260922
- **Meta-design** : `meta-design.yaml` (design talex-friction-analyzer)

---

## 9. Proof-of-Life

- [x] 2026-09-28T03:13:33+02:00 — Création de ce PRD-MOC.
- [ ] 2026-09-28T03:13:33+02:00 — Script KIX créé et testé.
- [ ] 2026-09-28T03:13:33+02:00 — Tests unitaires passent.
