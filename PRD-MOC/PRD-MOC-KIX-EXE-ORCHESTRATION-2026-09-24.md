---
type: "PRD_MOC"
citizen: "L2-PLATFORM"
layer: "L2"
author: gerivdb
source_repo: gerivdb/KIX
source_path: PRD-MOC/PRD-MOC-KIX-EXE-ORCHESTRATION-2026-09-24.md
parent_doc: PRD-MOC-KIX-MASTER.md
related_adr: ADR-2026-09-24-KIX-MULTI-LANG-RUNNERS.md, ADR-2026-08-18-002-KIX-GENERIC-RUNNER-WRAPPER.md
related_moc: PRD-MOC-KIX-MASTER.md, PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER-2026-09-27.md, PRD-MOC-KIX-MULTI-LANG-ECOSYSTEM-2026-09-24.md
version: "1.0.0"
date: "2026-09-27"
status: "partially_implemented"
intent_hash: "0xKIX_EXE_ORCHESTRATION_INTEGRATION_20260924"
mox_gates:
  - P-101
  - P-102
  - P-103
---

# PRD MOC - KIX - Orchestration des Exécutables, Preflight et Zombie Monitor

## 1. RESUME EXECUTIF

Ce PRD MOC couvre la refonte de l'orchestration des exécutables dans KIX autour de trois axes :

- **Taxonomie Toolchains vs Daemons** : séparer strictement les outils système/runtimes CLI des services applicatifs résidents.
- **Preflight & Diagnostics centralisés** : exposer `GET /preflight/status` et `POST /preflight/assert` pour le BOOT et l'Agent Manager.
- **Zombie Monitor intelligent** : croiser la détection processus avec le PID Registry des runners KIX pour éliminer les faux positifs.

**Source** : Rapport `reports/kix-exe-orchestration-report-2026-09-24.md` (v2.0)
**IntentHash** : `0xKIX_EXE_ORCHESTRATION_INTEGRATION_20260924`

---

## 2. ETAT ACTUEL

### 2.1 Taxonomie actuelle

| Exécutable | Classe actuelle | Rôle réel | Problème identifié |
|------------|-----------------|-----------|-------------------|
| `zig`, `python`, `node`, `cargo`, `bun`, `pwsh`, `git` | Traités comme processus génériques | Outils système / compilateurs (PATH) | `zombie_monitor.py` les inclut dans la liste de surveillance des zombies sans discrimination |
| `trixd`, `flex-api`, `kix`, `gateway-manager`, `batmcp` | Traités comme processus génériques | Daemons résidents (ports dédiés) | Pas de cycle de vie complet ni de PID Registry croisé |
| `zombie_monitor.py` | Surveillance aveugle | Détection d'orphelins | Liste codée en dur (`_ZOMBIE_PROCESS_NAMES`), critères génériques (CPU < 0.5%, RAM < 10MB, âge > 1h) |

### 2.2 Couverture KIX actuelle

| Composant | Fichier | Statut |
|-----------|---------|--------|
| Zombie monitor | `src/zombie_monitor.py` | 📄 Documenté |
| Diagnostics basiques | `src/diagnostics.py` | 📄 Documenté |
| Runners Python/Zig/Gateway | `runners/python_runner.py`, `runners/zig_runner.py`, `runners/gateway_runner.py` | 🔧 Implémenté |
| Registry runners | `runners/registry.py` | 🔧 Implémenté |
| Configuration déclarative | `config/runners.yaml` | 🔧 Implémenté |
| API REST | `src/app.py` | 🔧 Implémenté |

### 2.3 Gaps identifiés

| Gap | Impact |
|-----|--------|
| Pas de distinction toolchains / daemons | Faux positifs dans le zombie monitor, purge risquée d'outils système |
| Pas de PID Registry public | Impossible de discriminer processus légitimes vs orphelins |
| Pas de contrat `config/toolchains.yaml` | Les prérequis système ne sont pas déclaratifs |
| Pas d'endpoints `/preflight/*` | Le BOOT et l'Agent Manager ne peuvent pas valider l'infrastructure de façon standardisée |

---

## 3. ARCHITECTURE CIBLE

### 3.1 Principe fondateur

**KIX sépare l'infrastructure d'exécution en deux couches contractuelles** :

- **Toolchains & Runtimes CLI** : présence binaire, intégrité SHA256, version compatible, health check statutaire.
- **Services Applicatifs Daemons** : cycle de vie complet (start/stop/health/restart/rollback), PID Registry, ports dédiés.

### 3.2 Taxonomie cible

| Catégorie | Binaires concernés | Contrôle KIX |
|-----------|-------------------|--------------|
| **Toolchains & Runtimes CLI** | `zig`, `python`, `node`, `cargo`, `bun`, `pwsh`, `git` | Health check statutaire + preflight (`/preflight/status`, `/preflight/assert`) |
| **Services Applicatifs Daemons** | `trixd` (7243), `flex-api` (8820), `kix` (8800), `gateway-manager` (18000), `batmcp` (8000) | Cycle de vie complet + Doctor/Self-Healing + Swarm Status |

### 3.3 Contrats SOT vs Runtime State

- **SOT Déclarative** : `config/toolchains.yaml` (outils système) + `config/runners.yaml` (daemons).
- **Runtime State Cache** : `data/exe-state-registry.json` maintenu en temps réel par KIX (PIDs actifs, ports bindés, uptime, empreinte mémoire).

### 3.4 Détection intelligente des zombies

Un processus n'est candidat à la purge que si :

1. Son PID n'est **pas** dans le registre actif des runners KIX.
2. Il ne possède pas de fenêtre UI active.
3. Ses métriques CPU/RAM/Âge répondent aux critères de dérive sans activité.

### 3.5 Matrice de Preflight & Diagnostics

| Endpoint | Méthode | Rôle |
|----------|---------|------|
| `GET /preflight/status` | GET | Rapport d'état complet de l'infrastructure d'exécution |
| `POST /preflight/assert` | POST | Assertion contractuelle bloquante pour BOOT / Agent Manager (`{"require": ["zig", "trixd"]}`) |

---

## 4. PLAN D'IMPLEMENTATION

### Phase 1 : Contrat déclaratif toolchains
- [x] Créer `config/toolchains.yaml` : chemins, flags de version, timeouts.
- [ ] Ajouter la validation schématique YAML (P-101).

### Phase 2 : Diagnostics & Preflight
- [x] Implémenter `check_toolchains()` dans `src/diagnostics.py`.
- [x] Implémenter `check_daemon_health()` dans `src/diagnostics.py`.
- [x] Enregistrer `GET /preflight/status` et `POST /preflight/assert` dans `src/app.py`.
- [x] Tests unitaires préflight (`tests/test_preflight.py`).

### Phase 3 : Zombie Monitor intelligent
- [x] Raccorder `src/zombie_monitor.py` au PID Registry (`src/runner_state.py`).
- [x] Ajouter la règle de discrimination UI active / runner légitime.
- [x] Tests unitaires zombie monitor (`tests/test_zombie_monitor.py`).

### Phase 4 : SOT GOVERNANCE-HUB
- [x] Auditer `known_repositories.yaml` pour les repos critiques KIX/TRIX/FLEX/GATEWAY-MANAGER (`tests/test_sot_audit_pytest.py`).
- [ ] Enrichir `known_repositories.yaml` avec les champs `binary_target`, `runner_type`, `port` pour TRIX, KIX, FLEX, GATEWAY-MANAGER.
  - **Blocant** : KIX, TRIX et FLEX sont absents du SOT (`P0_REPOS`). Seul GATEWAY-MANAGER est présent et complet.
  - Action requise : ajout des entrées manquantes via PR vers `GOVERNANCE-HUB`.

### Phase 5 : Rollback & Self-Healing
- [x] Garantir l'arrêt de l'arborescence de processus enfants via JobObject Windows (`libs/shared-clients/win32_process.py`).
  - Helpers ajoutés : `create_job_object()`, `assign_process_to_job()`, `terminate_job()`.
  - Tests : `tests/test_win32_jobobject.py` (5 tests passants).
- [x] Ajouter la restauration automatique `.bak` + journalisation WAL (`data/kix-doctor.jsonl`).
  - Module `src/doctor_wal.py` : `create_backup()`, `restore_backup()`, `log_wal()`, `get_wal_entries()`.
  - Endpoint `/doctor/restore` intégré dans `src/app.py`.
  - WAL doctor activé dans `/doctor/run` pour chaque action de self-healing.
  - Tests : `tests/test_doctor_wal.py` (6 tests passants).

---

## 5. DEPENDANCES

### 5.1 Internes

| Fichier | Rôle |
|---------|------|
| `KIX/config/runners.yaml` | Registry déclaratif daemons |
| `KIX/config/toolchains.yaml` | **À créer** — registry déclaratif toolchains |
| `KIX/runners/base.py` | Interface `RunnerBase` |
| `KIX/runners/registry.py` | Registry runners + PID Registry |
| `KIX/src/diagnostics.py` | Diagnostics existants à étendre |
| `KIX/src/zombie_monitor.py` | Détection zombies à rendre intelligente |
| `KIX/src/app.py` | API REST à étendre avec `/preflight/*` |
| `KIX/libs/shared-clients/win32_process.py` | Primitives Win32 (JobObject) |
| `GOVERNANCE-HUB/known_repositories.yaml` | SOT repos → ajouter champs exécutables |

### 5.2 Externes

| Outil | Chemin | Usage |
|-------|--------|-------|
| `zig.exe` | `C:\DevTools\bin\zig\zig.exe` | Compilation TRIX/LLUX/ROOTX |
| `python.exe` | `C:\Users\GG\AppData\Local\Programs\Python\Python312\python.exe` | Services Python KIX/WAZAA/GATEWAY-MANAGER |
| `node.exe` | Via `npm`/`npx` | Services Node (si applicable) |
| `cargo.exe` | `C:\DevTools\.cargo\bin\cargo.exe` | Compilation services Rust (FLEX, TRIX) |
| `git.exe` | `C:\DevTools\git\cmd\git.exe` | Gestionnaire de versions |

---

## 6. TRACABILITE

### 6.1 Thought Chain

```yaml
thought_chain:
  - source: "Observation : zombie_monitor.py utilise une liste codée en dur sans discrimination runner/toolchain"
    artifact: "Risque de purge d'outils système légitimes"
    intent_hash: "0xKIX_EXE_ORCHESTRATION_INTEGRATION_20260924"
  - source: "Observation : pas de contrat déclaratif toolchains ni d'endpoints preflight standardisés"
    artifact: "BOOT et Agent Manager ne peuvent pas valider l'infrastructure de façon reproductible"
    intent_hash: "0xKIX_EXE_ORCHESTRATION_INTEGRATION_20260924"
```

### 6.2 Gates

| Gate | Critère | Statut |
|------|---------|--------|
| **P-101** | Conformité schéma YAML (`toolchains.yaml`, `runners.yaml`) | ✅ VALIDÉ |
| **P-102** | Forward references valides (`known_repositories.yaml` ↔ KIX configs) | ⏸️ PENDING (hors scope KIX seul) |
| **P-103** | Tests unitaires préflight + zombie monitor + doctor WAL ≥ 80% | ✅ VALIDÉ (102 tests passants) |

---

## 7. IMPLEMENTATION

| Livrable | Fichier | Statut |
|----------|---------|--------|
| Contrat toolchains YAML | `config/toolchains.yaml` | 🚀 Opérationnel |
| Diagnostics toolchains | `src/diagnostics.py::check_toolchains()` | 🚀 Opérationnel |
| Diagnostics daemons | `src/diagnostics.py::check_daemon_health()` | 🚀 Opérationnel |
| Endpoints preflight | `src/app.py::/preflight/status`, `/preflight/assert` | 🚀 Opérationnel |
| Zombie monitor intelligent | `src/zombie_monitor.py` (raccordement PID Registry) | 🚀 Opérationnel |
| Tests préflight | `tests/test_preflight.py` | 🧪 Testé |
| Tests zombie monitor | `tests/test_zombie_monitor.py` | 🧪 Testé |
| JobObject helpers | `libs/shared-clients/win32_process.py` | 🚀 Opérationnel |
| WAL doctor + .bak | `src/doctor_wal.py`, endpoint `/doctor/restore` | 🚀 Opérationnel |
| Tests JobObject | `tests/test_win32_jobobject.py` | 🧪 Testé |
| Tests doctor WAL | `tests/test_doctor_wal.py` | 🧪 Testé |
| Enrichissement SOT | `GOVERNANCE-HUB/known_repositories.yaml` (champs exécutables) | 📄 Documenté |

---

## 8. GLOSSAIRE DES STATUTS

- 📄 Documenté : artifact présent, frontmatter valide
- 🔧 Implémenté : code/config présent, pas encore testé
- 🧪 Testé : tests unitaires passants
- 🚀 Opérationnel : health-check OK, endpoint 200
- 🟢 Actif : dépendants actifs vérifiés
- 🟡 Passif : artifact présent, aucun dépendant actif
- ⏸️ Pending : blocage governance/HITL/ADR documenté
- ❌ Bloqué : dépendance manquante ou ADR refusé documenté

---

## 9. PROOF-OF-LIFE

- [x] 2026-09-24T00:00:00+02:00 — PRD-MOC EXE-ORCHESTRATION créé, phases 1-3 implémentées
- [x] 2026-09-27T04:00:00+02:00 — Phase 4 audit SOT complété (KIX/TRIX/FLEX manquent du SOT, GATEWAY-MANAGER présent)
- [x] 2026-09-27T06:01:00+02:00 — Phase 5 implémentée : JobObject helpers (5 tests), WAL doctor + .bak restore (6 tests), `/doctor/restore` endpoint
- [x] 2026-09-27T06:01:00+02:00 — 102 tests passants, gates P-101/P-103 validés, P-102 hors scope KIX seul

---

## 10. REFERENCES

- `reports/kix-exe-orchestration-report-2026-09-24.md` : Rapport initial (v1)
- `PRD-MOC-KIX-ORCHESTRATOR-2026-08-18.md` : PRD MOC orchestrateur generic runner wrapper
- `PRD-MOC-KIX-MASTER.md` : Master MOC KIX
- `PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-2026-09-24.md` : Intégration maître écosystème
- `PRD-MOC-KIX-MULTI-LANG-ECOSYSTEM-2026-09-24.md` : Intégration multi-langages
- `ADR-2026-09-24-KIX-MULTI-LANG-RUNNERS.md` : ADR runners multi-langages
- `GOVERNANCE-HUB/known_repositories.yaml` : SOT des repos
- `src/zombie_monitor.py` : Module de détection zombies
- `src/diagnostics.py` : Module de diagnostics KIX


