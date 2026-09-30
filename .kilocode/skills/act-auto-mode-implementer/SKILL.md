---
name: act-auto-mode-implementer
description: Skill d'implémentation automatique en mode ACT (Atomic, Causal, Test-first). Utilise ATOM-KIX-ACT-AUTO-MODE pour décomposer les tâches en étapes atomiques, écrire les tests d'abord, implémenter le minimum, vérifier la cause racine, et committer.
version: 1.0.0
intent_hash: 0xSKILL_ACT_AUTO_MODE_IMPLEMENTER_20260930
---

# ACT Auto Mode Implementer

## Objectif
Implémenter automatiquement les gaps identifiés par TALEX engine en mode ACT :
- **Atomic** : une tâche = un outil = un résultat vérifiable
- **Causal** : corriger la cause racine, pas le symptôme
- **Test-first** : écrire le test qui échoue avant l'implémentation
- **Auto** : exécution automatique sans intervention humaine entre les étapes
- **SLM-calibrated** : tâches calibrées pour les capacités du Small Language Model

## Workflow

### Étape 1 — Analyser le gap
```
TALEX engine → détecte friction/ERR/couverture
→ Classifie : connu/inédit, structurel/causal, P0/P1/P2/P3
→ Propose correction atomique
```

### Étape 2 — Créer le test qui échoue (test-first)
```python
def test_gap_coverage():
    # Test qui échoue initialement
    # Couvre la branche manquante identifiée par pytest-cov
    ...
```

### Étape 3 — Implémenter le minimum (atomic)
```python
# Implémenter uniquement ce qui fait passer le test
# Pas de code superflu
```

### Étape 4 — Vérifier la cause racine (causal)
```
Pourquoi la branche était manquante ?
→ ImportError non géré ? → Ajouter try/except + test
→ Branche conditionnelle ? → Ajouter test pour chaque condition
→ Code mort ? → Supprimer le code
```

### Étape 5 — Committer atomiquement
```bash
git add <fichiers_concernés>
git commit -m "test(coverage): cover <branche> in <module>

- Add test for <scenario>
- Fix <root_cause>
- Coverage: <module> <avant>% → <après>%"
```

### Étape 6 — Passer au gap suivant
```
→ Re-lancer pytest --cov=src --cov-report=term-missing
→ Identifier le prochain gap
→ Répéter Étape 1 à 5
```

## SLM Calibration

| Taille de tâche | Calibre SLM | Action |
|-----------------|-------------|--------|
| < 10 lignes de code | Atomic direct | Implémenter en une étape |
| 10-50 lignes | Fragmenté | 2-3 étapes max |
| > 50 lignes | Décomposer | Sous-tâches atomiques |
| Scan multi-fichiers | Interdit | Utiliser grep/glob ciblé |
| Regex Unicode | Interdit | Outils existants |

## Anti-patterns

- ❌ Implémenter sans test d'abord
- ❌ Corriger le symptôme au lieu de la cause racine
- ❌ Commit batch avec > 3 fichiers
- ❌ Tâche > 50 lignes sans décomposition
- ❌ Ignorer les ERR-KIX-* documentées

## Références

- Atome : `ATOM-KIX-ACT-AUTO-MODE`
- Atome : `ATOM-KIX-SLM-CALIBRATION`
- Atome : `ATOM-KIX-COVERAGE-GAP-FILLER`
- ERR : `ERR-KIX-001` à `ERR-KIX-009`
- PRD-MOC : `PRD-MOC-KIX-TEST-COVERAGE-100-20260929.md`
