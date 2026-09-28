---
owner: L2-PLATFORM

type: PRD-MOC
version: "1.0.0"
date: "2026-09-28"
status: approved
intent_hash: 0xPRD_MOC_KIX_SESSION_BOOT_DESIGN_CONSUMER_20260928
citizen: "L2-KIX"
layer: "L2"
author: gerivdb
source_repo: gerivdb/KIX
source_path: PRD-MOC/PRD-MOC-KIX-SESSION-BOOT-DESIGN-CONSUMER-20260928.md
pole_id: POLE-KG-TDC-001
---

# PRD MOC - KIX Session Boot Design Consumer

> **Verdict** : PRD_MOC — Rendre obligatoire l'application du design `session-boot-design` dans KIX.
> **Source** : Design `session-boot-design` (`designs/session-boot-design/design.yaml`), PRD-MOC-SESSION-BOOT-20260920.
> **Constat** : KIX est consumer de `session-boot-design` mais n'a pas de PRD-MOC local déclarant cette obligation.

---

## 1. Contexte

KIX est un consumer du design `session-boot-design`. Toute session KIX DOIT passer par BOOT/CLOSEOUT standardisés.

---

## 2. Problème

| Symptôme | Cause racine | Impact |
|----------|--------------|--------|
| Sessions sans BOOT | Design non appliqué | Frictions non détectées |
| Sessions sans CLOSEOUT | Design non appliqué | Working tree sale |

---

## 3. Objectif

Intégrer les checks BOOT/CLOSEOUT dans toutes les sessions KIX.

---

## 4. Périmètre

### 4.1 In Scope

| Opération | Application |
|-----------|-------------|
| Déploiement | BOOT checks automatiques |
| Configuration | CLOSEOUT checks automatiques |

### 4.2 Out of Scope

- Modification du design `session-boot-design` lui-même
- Autres CLIs

---

## 5. Architecture

### 5.1 Intégration KIX

```python
# kix/pipelines/session_boot.py
from session_boot_design import SessionBoot

class SessionBootKix:
    def start(self):
        boot = SessionBoot()
        boot.run_boot_checks()
    
    def end(self):
        boot = SessionBoot()
        boot.run_closeout_checks()
```

---

## 6. Livrables

| ID | Livrable | Chemin cible | Type |
|---|---|---|---|
| L1 | PRD-MOC `session-boot-design` | `PRD-MOC/PRD-MOC-KIX-SESSION-BOOT-DESIGN-CONSUMER-20260928.md` | Créer |
| L2 | Script KIX | `kix/pipelines/session_boot.py` | Créer |
| L3 | Tests unitaires | `tests/test_session_boot_kix.py` | Créer |

---

## 7. Critères d'acceptation

1. `session_boot.py` exécute les checks BOOT/CLOSEOUT.
2. Tests unitaires passent.
3. Proof-of-Life horodatée dans ce PRD-MOC.

---

## 8. Références

- **Design** : `designs/session-boot-design/design.yaml`
- **PRD-MOC** : PRD-MOC-SESSION-BOOT-20260920
- **Meta-design** : `meta-design.yaml` (design session-boot-design)

---

## 9. Proof-of-Life

- [x] 2026-09-28T03:13:33+02:00 — Création de ce PRD-MOC.
- [ ] 2026-09-28T03:13:33+02:00 — Script KIX créé et testé.
- [ ] 2026-09-28T03:13:33+02:00 — Tests unitaires passent.
