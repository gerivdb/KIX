---
owner: L2-PLATFORM

type: PRD-MOC
version: "1.0.0"
date: "2026-09-28"
status: approved
intent_hash: 0xPRD_MOC_KIX_ARTIFACT_LAYERS_DESIGN_CONSUMER_20260928
citizen: "L2-KIX"
layer: "L2"
author: gerivdb
source_repo: gerivdb/KIX
source_path: PRD-MOC/PRD-MOC-KIX-ARTIFACT-LAYERS-DESIGN-CONSUMER-20260928.md
pole_id: POLE-KG-TDC-001
---

# PRD MOC - KIX Artifact Layers Design Consumer

> **Verdict** : PRD_MOC — Rendre obligatoire l'application du design `artifact-layers-design` dans KIX.
> **Source** : Design `artifact-layers-design` (`designs/artifact-layers-design/design.yaml`), PRD-MOC-ARTIFACT-LAYERS-20260921.
> **Constat** : KIX est consumer de `artifact-layers-design` mais n'a pas de PRD-MOC local déclarant cette obligation.

---

## 1. Contexte

KIX est un consumer du design `artifact-layers-design`. Toute opération KIX DOIT respecter les couches d'artefacts (core, adapter, presentation).

---

## 2. Problème

| Symptôme | Cause racine | Impact |
|----------|--------------|--------|
| Opérations sans couches | Design non appliqué | Architecture incohérente |
| mélange des responsabilités | Design non appliqué | dette technique |

---

## 3. Objectif

Intégrer les couches d'artefacts dans toutes les opérations KIX.

---

## 4. Périmètre

### 4.1 In Scope

| Opération | Application |
|-----------|-------------|
| Déploiement | Couches d'artefacts respectées |
| Configuration | Couches d'artefacts respectées |
| Orchestration | Couches d'artefacts respectées |

### 4.2 Out of Scope

- Modification du design `artifact-layers-design` lui-même
- Opérations en lecture seule

---

## 5. Architecture

### 5.1 Intégration KIX

```python
# kix/pipelines/artifact_layers.py
from artifact_layers_design import ArtifactLayers

class ArtifactLayersKix:
    def validate(self, context):
        layers = ArtifactLayers()
        return layers.validate(context)
```

---

## 6. Livrables

| ID | Livrable | Chemin cible | Type |
|---|---|---|---|
| L1 | PRD-MOC `artifact-layers-design` | `PRD-MOC/PRD-MOC-KIX-ARTIFACT-LAYERS-DESIGN-CONSUMER-20260928.md` | Créer |
| L2 | Script KIX | `kix/pipelines/artifact_layers.py` | Créer |
| L3 | Tests unitaires | `tests/test_artifact_layers_kix.py` | Créer |

---

## 7. Critères d'acceptation

1. `artifact_layers.py` valide les couches d'artefacts.
2. Tests unitaires passent.
3. Proof-of-Life horodatée dans ce PRD-MOC.

---

## 8. Références

- **Design** : `designs/artifact-layers-design/design.yaml`
- **PRD-MOC** : PRD-MOC-ARTIFACT-LAYERS-20260921
- **Meta-design** : `meta-design.yaml` (design artifact-layers-design)

---

## 9. Proof-of-Life

- [x] 2026-09-28T03:13:33+02:00 — Création de ce PRD-MOC.
- [ ] 2026-09-28T03:13:33+02:00 — Script KIX créé et testé.
- [ ] 2026-09-28T03:13:33+02:00 — Tests unitaires passent.
