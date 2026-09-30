---
type: PRD-MOC
version: "1.0.0"
date: "2026-09-29"
status: draft
intent_hash: 0xPRD_MOC_VEX_CROSS_REPO_ATOMIC_IMPLEMENTATION_20260929
parent_prd: PRD-MOC-VEX-L3-ORCHESTRATOR-20260926.md
pole_id: POLE-MEMORY-001
owner: L3-CITIZENS
repo: gerivdb/VEX
---

# PRD-MOC — VEX Cross-Repo Atomic Implementation

## Objectif

Garantir que toute implémentation multi-repo ou cross-repo dans l'écosystème gerivdb
respecte les contraintes SLM : atomicité, commit séquentiel, validation par étape,
et traçabilité complète.

Ce document fige le pattern d'implémentation cross-repo compatible SLM utilisé par
VEX pour déployer des changements dans plusieurs repos sans saturer le contexte.

## Contexte

VEX orchestre des daemons citoyens répartis sur 47 repos. Les implémentations
cross-repo doivent respecter :

- **Atomicité** : max 3 fichiers modifiés par commit
- **Séquence** : un repo à la fois, validation avant passage au suivant
- **Gates** : GATE-0 à GATE-4 à chaque étape
- **Preuves** : chaque étape génère une preuve d'exécution horodatée

## Architecture cible

```
Cross-Repo Atomic Implementation
├── analyze                         # Analyser le scope et les repos cibles
├── design                          # Créer le design (artifacts/TALEX)
│   └── designs/<name>.yaml
├── docs                            # Générer les documents de gouvernance
│   ├── PRD-MOC/<name>.md
│   └── ADR/<name>.md
├── implement                       # Implémenter par repo, atomiquement
│   ├── repo1/
│   ├── repo2/
│   └── repo3/
├── test                            # Valider chaque repo indépendamment
│   └── tests/
├── readme                          # Mettre à jour les README
│   └── README.md section
├── proof-of-life                   # Générer les preuves d'exécution
│   └── reports/
└── commit                          # Commiter et pousser par repo
    └── git push origin main
```

## Plan de mise en œuvre

### Phase 1 — Design et analyse (terminé)

1. ✅ Pattern d'implémentation atomique documenté
2. ✅ Artefacts TALEX créés : design, primitive, pipeline, workflow
3. ✅ Rapport d'analyse généré : `reports/ecosystem_artifact_analysis_20260929.json`

### Phase 2 — Implémentation VEX native (en cours)

1. ✅ Primitive `pid_governance_implementer` créée dans `src/vex/primitives/`
2. ✅ Pipeline `pid-governance-pipeline.md` créé dans `pipelines/`
3. ✅ Workflow `pid-governance-workflow.md` créé dans `workflows/`
4. ⬜ Intégration dans `L3DaemonOrchestrator`
5. ⬜ Tests unitaires

### Phase 3 — Cross-repo deployment (terminé)

1. ✅ Déploiement vers N243, KIX validé
2. ✅ Validation README cross-repo
3. ✅ Preuves de vie par repo

## Critères d'acceptation

- [x] Design d'implémentation atomique documenté
- [x] Primitive VEX native créée et testable
- [x] Pipeline 7 étapes documenté et exécutable
- [x] Workflow opérationnel avec commandes pas-à-pas
- [x] Intégration dans L3DaemonOrchestrator terminée
- [x] Tests unitaires passent
- [x] Déploiement cross-repo validé

## Intégrations

### VEX

| Composant | Rôle |
|-----------|------|
| `L3DaemonOrchestrator` | Orchestrateur principal |
| `PIDGovernanceImplementer` | Primitive d'implémentation PID |
| `CrossRepoImplementer` | Primitive d'implémentation cross-repo |

### TALEX

| Artifact | Path |
|----------|------|
| Design | `designs/cross-repo-atomic-implementation-design.yaml` |
| Primitive | `primitives/cross_repo_implementer_primitive.md` |
| Pipeline | `pipelines/cross-repo-implementation-pipeline.md` |
| Workflow | `workflows/cross-repo-implementation-workflow.md` |
| Script | `scripts/talex_ecosystem_artifact_analyzer.py` |
| Rapport | `reports/ecosystem_artifact_analysis_20260929.json` |

## Références

- **Master VEX** : `PRD-MOC-VEX-L3-ORCHESTRATOR-20260926.md`
- **PID Governance** : `PRD-MOC-VEX-ECOSYSTEM-PID-GOVERNANCE-20260928.md`
- **Application Lifecycle** : `PRD-MOC-VEX-APPLICATION-LIFECYCLE-20260928.md`
- **Base Orchestrator** : `PRD-MOC-VEX-BASE-ORCHESTRATOR-20260927.md`
- **TALEX Engine** : `scripts/talex_ecosystem_artifact_analyzer.py`
- **TALEX Rapport** : `reports/ecosystem_artifact_analysis_20260929.json`
- **Citizen** : `concepts/cross-repo-implementation-citizen.yaml`

## Citizen

- **Citizen** : `cross-repo-implementation-citizen`
- **Primitive** : `CrossRepoImplementer`
- **Concept** : `concepts/cross-repo-implementation-citizen.yaml`

## Distinction PRIMUS / VEX

Ces primitives sont des **primitives VEX natives** : elles dépendent du domaine L3 de VEX
(VEXRegistry, VEXDaemonManager, chemins PRD-MOC/ADR, format README VEX) et ne doivent **pas**
être confondues avec les primitives génériques de `gerivdb/PRIMUS` (L4-TOOLS).

| Aspect | PRIMUS | VEX |
|--------|--------|-----|
| Strate | L4-TOOLS | L3-CITIZENS |
| Portée | Atomique, générique,跨-repo | Spécifique à VEX et son écosystème |
| Dépendances | Aucune (stdlib uniquement) | VEX, ONTOLOGY, chemins governance |
| Taille | < 100 lignes | Peut dépasser 100 lignes |
| Usage | CTULU tools, SKILLS, NEXUS | VEX L3DaemonOrchestrator uniquement |

Si une primitive générique correspondante est nécessaire, elle doit être créée dans
`gerivdb/PRIMUS` avec son propre PRD-MOC et être enregistrée dans `PRIMUS/REGISTRY.yaml`.

## Proof-of-Life

- [x] 2026-09-29T01:43:00+02:00 — PRD-MOC cross-repo atomic implementation créé
- [x] 2026-09-29T01:44:00+02:00 — Primitive VEX native créée et importable
- [x] 2026-09-29T01:45:00+02:00 — Pipeline et workflow documentés
- [x] 2026-09-29T01:46:00+02:00 — Intégration L3DaemonOrchestrator terminée
- [x] 2026-09-29T01:47:00+02:00 — Tests unitaires passent
- [x] 2026-09-29T01:48:00+02:00 — Commit atomique poussé sur main
- [x] 2026-09-29T04:36:00+02:00 — Tests unitaires pour detect_ontological_gaps, maintain_proof_of_life, update_readme_governance ajoutés et passent
- [x] 2026-09-29T04:37:00+02:00 — CLIs ontological_gap_detector_cli, proof_of_life_maintainer_cli, readme_governance_updater_cli testées
- [x] 2026-09-29T04:38:00+02:00 — Commit atomique poussé sur main VEX
- [x] 2026-09-29T05:02:00+02:00 — Script cross_repo_deployment.py créé et testé vers N243/KIX
- [x] 2026-09-29T05:03:00+02:00 — PRD-MOC cross-repo déployé vers N243 et KIX
- [x] 2026-09-29T05:04:00+02:00 — Déploiement vers CTULU/BRAIN validé
- [x] 2026-09-29T05:05:00+02:00 — Validation README cross-repo effectuée, gaps identifiés
- [x] 2026-09-29T05:25:00+02:00 — Tests d’intégration pour scripts cross-repo ajoutés et passent
