# Audit Custom Runners vs SOT — KIX (2026-09-28)

## Contexte
Les custom runners de `config/runners.yaml` référencent des repos `gerivdb/*` qui ne sont pas présents dans `known_repositories.yaml`. Ce document liste les écarts et propose des actions.

## Résultat

| Catégorie | Nombre |
|-----------|--------|
| Custom runners totaux | 31 |
| Présents dans SOT | 0 |
| Absents du SOT | 31 |

## Liste des runners absents du SOT

| Runner | Repo référencé |
|--------|---------------|
| gitex | gerivdb/gitex |
| repoxt | gerivdb/repoxt |
| syncx | gerivdb/syncx |
| referex | gerivdb/referex |
| kglx | gerivdb/kglx |
| harnex | gerivdb/harnex |
| telox | gerivdb/telox |
| timx | gerivdb/timx |
| rlm243 | gerivdb/rlm243 |
| causex | gerivdb/causex |
| morphex | gerivdb/morphex |
| identx | gerivdb/identx |
| topex | gerivdb/topex |
| chronox | gerivdb/chronox |
| llux-match | gerivdb/llux-match |
| llux-index | gerivdb/llux-index |
| prognex | gerivdb/prognex |
| llux-learn | gerivdb/llux-learn |
| llux-replay | gerivdb/llux-replay |
| timx-feature-store | gerivdb/timx-feature-store |
| rlm-mdu | gerivdb/rlm-mdu |
| deployex | gerivdb/deployex |
| flowx | gerivdb/flowx |
| llm-core | gerivdb/llm-core |
| piano | gerivdb/piano |
| trix | gerivdb/trix |
| conversation-cognitive | gerivdb/conversation-cognitive |
| flex | gerivdb/flex |
| infx | gerivdb/infx |
| codedb-e5620 | gerivdb/codedb-e5620 |
| nexus | gerivdb/nexus |

## Actions recommandées

1. **Court terme** : ajouter les entrées manquantes dans `known_repositories.yaml` via PR GOVERNANCE-HUB.
2. **Moyen terme** : vérifier pour chaque repo absent si le clone local existe ; si oui, lier via `local_path`.
3. **Gouvernance** : tout nouveau custom runner doit être référencé dans le SOT avant d'être ajouté dans `runners.yaml`.

## Référence

- `config/runners.yaml` : 31 custom runners
- `known_repositories.yaml` : 0 entrée correspondante
- PRD-MOC : PRD-MOC-KIX-EXE-ORCHESTRATION-2026-09-24.md Phase 4
