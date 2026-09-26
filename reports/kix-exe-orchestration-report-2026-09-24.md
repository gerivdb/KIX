# Rapport d'orchestration KIX - Exécutables, Preflight et Zombie Monitor
**Date :** 2026-09-24
**Version :** v2.0
**IntentHash :** `0xKIX_EXE_ORCHESTRATION_INTEGRATION_20260924`

---

## 1. Synthèse

KIX doit séparer strictement :
- **Toolchains & Runtimes CLI** : `zig`, `python`, `node`, `cargo`, `bun`, `pwsh`, `git`
- **Services Applicatifs Daemons** : `trixd`, `flex-api`, `kix`, `gateway-manager`, `batmcp`

## 2. Architecture cible

- `config/toolchains.yaml` comme SOT déclarative des outils système
- `config/runners.yaml` comme SOT déclarative des daemons
- `data/exe-state-registry.json` comme runtime state cache
- `/preflight/status` et `/preflight/assert` comme endpoints standardisés
- `zombie_monitor.py` raccordé au PID Registry des runners KIX

## 3. Plan d'implémentation

### Phase 1 : Contrat déclaratif toolchains
- Créer `config/toolchains.yaml`
- Validation schématique YAML (P-101)

### Phase 2 : Diagnostics & Preflight
- Implémenter `check_toolchains()` et `check_daemon_health()` dans `src/diagnostics.py`
- Enregistrer `GET /preflight/status` et `POST /preflight/assert` dans `src/app.py`
- Tests unitaires préflight

### Phase 3 : Zombie Monitor intelligent
- Raccorder `src/zombie_monitor.py` au PID Registry (`runners/registry.py`)
- Ajouter la règle de discrimination UI active / runner légitime
- Tests unitaires zombie monitor

### Phase 4 : SOT GOVERNANCE-HUB
- Enrichir `known_repositories.yaml` avec les champs `binary_target`, `runner_type`, `port`

### Phase 5 : Rollback & Self-Healing
- Garantir l'arrêt de l'arborescence de processus enfants via JobObject Windows
- Ajouter la restauration automatique `.bak` + journalisation WAL (`data/kix-doctor.jsonl`)

## 4. Livrables

| Livrable | Fichier | Statut |
|----------|---------|--------|
| Contrat toolchains YAML | `config/toolchains.yaml` | Documenté |
| Diagnostics toolchains | `src/diagnostics.py::check_toolchains()` | Documenté |
| Diagnostics daemons | `src/diagnostics.py::check_daemon_health()` | Documenté |
| Endpoints preflight | `src/app.py::/preflight/status`, `/preflight/assert` | Documenté |
| Zombie monitor intelligent | `src/zombie_monitor.py` | Documenté |
| Enrichissement SOT | `GOVERNANCE-HUB/known_repositories.yaml` | Documenté |
| Rollback JobObject | `libs/shared-clients/win32_process.py` | Documenté |
| Tests préflight | `tests/test_preflight.py` | Documenté |
| Tests zombie monitor | `tests/test_zombie_monitor.py` (extension) | Documenté |

## 5. Références

- `PRD-MOC-KIX-EXE-ORCHESTRATION-2026-09-24.md` : PRD MOC associé
- `PRD-MOC-KIX-ORCHESTRATOR-2026-08-18.md` : PRD MOC orchestrateur generic runner wrapper
- `PRD-MOC-KIX-MASTER.md` : Master MOC KIX
- `ADR-2026-09-24-KIX-MULTI-LANG-RUNNERS.md` : ADR runners multi-langages
- `GOVERNANCE-HUB/known_repositories.yaml` : SOT des repos
