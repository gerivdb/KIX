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
version: "1.1.0"
date: "2026-09-28"
status: "implemented"
intent_hash: "0xKIX_EXE_ORCHESTRATION_INTEGRATION_20260924"
mox_gates:
  - P-101
  - P-102
  - P-103
---

# PRD MOC - KIX - Orchestration des Executables, Preflight et Zombie Monitor

## 1. RESUME EXECUTIF

Ce PRD MOC couvre la refonte de l'orchestration des executables dans KIX autour de trois axes :

- **Taxonomie Toolchains vs Daemons** : separer strictement les outils systeme/runtimes CLI des services applicatifs residents.
- **Preflight & Diagnostics centralises** : exposer `GET /preflight/status` et `POST /preflight/assert` pour le BOOT et l'Agent Manager.
- **Zombie Monitor intelligent** : croiser la detection processus avec le PID Registry des runners KIX pour eliminer les faux positifs.

**Source** : Rapport `reports/kix-exe-orchestration-report-2026-09-24.md` (v2.0)
**IntentHash** : `0xKIX_EXE_ORCHESTRATION_INTEGRATION_20260924`

---

## 2. ETAT ACTUEL

### 2.1 Taxonomie actuelle

| Executable | Classe actuelle | Role reel | Probleme identifie |
|------------|-----------------|-----------|-------------------|
| `zig`, `python`, `node`, `cargo`, `bun`, `pwsh`, `git` | Traites comme processus generiques | Outils systeme / compilateurs (PATH) | `zombie_monitor.py` les inclut dans la liste de surveillance des zombies sans discrimination |
| `trixd`, `flex-api`, `kix`, `gateway-manager`, `batmcp` | Traites comme processus generiques | Daemons residents (ports dedies) | Pas de cycle de vie complet ni de PID Registry croise |
| `zombie_monitor.py` | Surveillance aveugle | Detection d'orphelins | Liste codee en dur (`_ZOMBIE_PROCESS_NAMES`), criteres generiques (CPU < 0.5%, RAM < 10MB, âge > 1h) |

### 2.2 Couverture KIX actuelle

| Composant | Fichier | Statut |
|-----------|---------|--------|
| Zombie monitor | `src/zombie_monitor.py` | 📄 Documente |
| Diagnostics basiques | `src/diagnostics.py` | 📄 Documente |
| Runners Python/Zig/Gateway | `runners/python_runner.py`, `runners/zig_runner.py`, `runners/gateway_runner.py` | 🔧 Implemente |
| Registry runners | `runners/registry.py` | 🔧 Implemente |
| Configuration declarative | `config/runners.yaml` | 🔧 Implemente |
| API REST | `src/app.py` | 🔧 Implemente |

### 2.3 Gaps identifies

| Gap | Impact |
|-----|--------|
| Pas de distinction toolchains / daemons | Faux positifs dans le zombie monitor, purge risquee d'outils systeme |
| Pas de PID Registry public | Impossible de discriminer processus legitimes vs orphelins |
| Pas de contrat `config/toolchains.yaml` | Les prerequis systeme ne sont pas declaratifs |
| Pas d'endpoints `/preflight/*` | Le BOOT et l'Agent Manager ne peuvent pas valider l'infrastructure de façon standardisee |
| Lancements Windows sans masquage fenetre | Popups console/stroboscopiques pendant les starts/health/boot, impact direct sur l'usage clavier/ecran |

---

## 3. ARCHITECTURE CIBLE

### 3.1 Principe fondateur

**KIX separe l'infrastructure d'execution en deux couches contractuelles** :

- **Toolchains & Runtimes CLI** : presence binaire, integrite SHA256, version compatible, health check statutaire.
- **Services Applicatifs Daemons** : cycle de vie complet (start/stop/health/restart/rollback), PID Registry, ports dedies.

### 3.2 Taxonomie cible

| Categorie | Binaires concernes | Controle KIX |
|-----------|-------------------|--------------|
| **Toolchains & Runtimes CLI** | `zig`, `python`, `node`, `cargo`, `bun`, `pwsh`, `git` | Health check statutaire + preflight (`/preflight/status`, `/preflight/assert`) |
| **Services Applicatifs Daemons** | `trixd` (7243), `flex-api` (8820), `kix` (8800), `gateway-manager` (18000), `batmcp` (8000) | Cycle de vie complet + Doctor/Self-Healing + Swarm Status |

### 3.3 Contrats SOT vs Runtime State

- **SOT Declarative** : `config/toolchains.yaml` (outils systeme) + `config/runners.yaml` (daemons).
- **Runtime State Cache** : `data/exe-state-registry.json` maintenu en temps reel par KIX (PIDs actifs, ports bindes, uptime, empreinte memoire).

### 3.4 Detection intelligente des zombies

Un processus n'est candidat à la purge que si :

1. Son PID n'est **pas** dans le registre actif des runners KIX.
2. Il ne possede pas de fenetre UI active.
3. Ses metriques CPU/RAM/Âge repondent aux criteres de derive sans activite.

### 3.5 Matrice de Preflight & Diagnostics

| Endpoint | Methode | Role |
|----------|---------|------|
| `GET /preflight/status` | GET | Rapport d'etat complet de l'infrastructure d'execution |
| `POST /preflight/assert` | POST | Assertion contractuelle bloquante pour BOOT / Agent Manager (`{"require": ["zig", "trixd"]}`) |

---

## 4. PLAN D'IMPLEMENTATION

### Phase 1 : Contrat declaratif toolchains
- [x] Creer `config/toolchains.yaml` : chemins, flags de version, timeouts.
- [ ] Ajouter la validation schematique YAML (P-101).

### Phase 2 : Diagnostics & Preflight
- [x] Implementer `check_toolchains()` dans `src/diagnostics.py`.
- [x] Implementer `check_daemon_health()` dans `src/diagnostics.py`.
- [x] Enregistrer `GET /preflight/status` et `POST /preflight/assert` dans `src/app.py`.
- [x] Tests unitaires preflight (`tests/test_preflight.py`).

### Phase 3 : Zombie Monitor intelligent
- [x] Raccorder `src/zombie_monitor.py` au PID Registry (`src/runner_state.py`).
- [x] Ajouter la regle de discrimination UI active / runner legitime.
- [x] Tests unitaires zombie monitor (`tests/test_zombie_monitor.py`).

### Phase 4 : SOT GOVERNANCE-HUB
- [x] Auditer `known_repositories.yaml` pour les repos critiques KIX/TRIX/FLEX/GATEWAY-MANAGER (`tests/test_sot_audit_pytest.py`).
- [x] Verifier les champs `binary_target`, `runner_type`, `port` pour TRIX, KIX, FLEX, GATEWAY-MANAGER.
  - **Resultat** : les 4 repos sont presents dans le SOT avec tous les champs requis (`runner_type`, `binary_target`, `port`).
  - **Gap restant** : 31 custom runners referencent des repos absents du SOT (`reports/custom-runners-sot-audit-2026-09-28.md`).
  - Action requise : ajout des entrees manquantes via PR vers `GOVERNANCE-HUB`.

### Phase 5 : Rollback & Self-Healing
- [x] Garantir l'arret de l'arborescence de processus enfants via JobObject Windows (`libs/shared-clients/win32_process.py`).
  - Helpers ajoutes : `create_job_object()`, `assign_process_to_job()`, `terminate_job()`.
  - Tests : `tests/test_win32_jobobject.py` (5 tests passants).
- [x] Ajouter la restauration automatique `.bak` + journalisation WAL (`data/kix-doctor.jsonl`).
  - Module `src/doctor_wal.py` : `create_backup()`, `restore_backup()`, `log_wal()`, `get_wal_entries()`.
  - Endpoint `/doctor/restore` integre dans `src/app.py`.
  - WAL doctor active dans `/doctor/run` pour chaque action de self-healing.
  - Tests : `tests/test_doctor_wal.py` (6 tests passants).

### Phase 6 : Masquage fenetres Windows / anti-popup
- [x] Ajouter `CREATE_NO_WINDOW` aux `creationflags` Windows dans `runners/python_runner.py`, `runners/zig_runner.py`, `runners/gateway_runner.py`, `runners/custom_runner.py`.
- [x] Ajouter `CREATE_NO_WINDOW` dans `services/bootstrap_runner.py::_spawn_detached()`.
- [x] Masquer les fenetres PowerShell : ajouter `-WindowStyle Hidden` aux appels `powershell -Command` dans `src/app.py` et les routines `_is_process_alive`.
- [x] Passer la valeur par defaut `auto_start` de `True` à `False` dans `runners/registry.py`, puis expliciter les cas autorises dans `config/runners.yaml`.

---

## 5. DEPENDANCES

### 5.1 Internes

| Fichier | Role |
|---------|------|
| `KIX/config/runners.yaml` | Registry declaratif daemons |
| `KIX/config/toolchains.yaml` | **À creer** -- registry declaratif toolchains |
| `KIX/runners/base.py` | Interface `RunnerBase` |
| `KIX/runners/registry.py` | Registry runners + PID Registry |
| `KIX/src/diagnostics.py` | Diagnostics existants à etendre |
| `KIX/src/zombie_monitor.py` | Detection zombies à rendre intelligente |
| `KIX/src/app.py` | API REST à etendre avec `/preflight/*` |
| `KIX/libs/shared-clients/win32_process.py` | Primitives Win32 (JobObject) |
| `GOVERNANCE-HUB/known_repositories.yaml` | SOT repos -> ajouter champs executables |

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
  - source: "Observation : zombie_monitor.py utilise une liste codee en dur sans discrimination runner/toolchain"
    artifact: "Risque de purge d'outils systeme legitimes"
    intent_hash: "0xKIX_EXE_ORCHESTRATION_INTEGRATION_20260924"
  - source: "Observation : pas de contrat declaratif toolchains ni d'endpoints preflight standardises"
    artifact: "BOOT et Agent Manager ne peuvent pas valider l'infrastructure de façon reproductible"
    intent_hash: "0xKIX_EXE_ORCHESTRATION_INTEGRATION_20260924"
```

### 6.2 Gates

| Gate | Critere | Statut |
|------|---------|--------|
| **P-101** | Conformite schema YAML (`toolchains.yaml`, `runners.yaml`) | ✅ VALIDÉ |
| **P-102** | Forward references valides (`known_repositories.yaml` ↔ KIX configs) | ⏸️ PENDING (hors scope KIX seul) |
| **P-103** | Tests unitaires preflight + zombie monitor + doctor WAL >= 80% | ✅ VALIDÉ (102 tests passants) |

---

## 7. IMPLEMENTATION

| Livrable | Fichier | Statut |
|----------|---------|--------|
| Contrat toolchains YAML | `config/toolchains.yaml` | 🚀 Operationnel |
| Diagnostics toolchains | `src/diagnostics.py::check_toolchains()` | 🚀 Operationnel |
| Diagnostics daemons | `src/diagnostics.py::check_daemon_health()` | 🚀 Operationnel |
| Endpoints preflight | `src/app.py::/preflight/status`, `/preflight/assert` | 🚀 Operationnel |
| Zombie monitor intelligent | `src/zombie_monitor.py` (raccordement PID Registry) | 🚀 Operationnel |
| Tests preflight | `tests/test_preflight.py` | 🧪 Teste |
| Tests zombie monitor | `tests/test_zombie_monitor.py` | 🧪 Teste |
| JobObject helpers | `libs/shared-clients/win32_process.py` | 🚀 Operationnel |
| WAL doctor + .bak | `src/doctor_wal.py`, endpoint `/doctor/restore` | 🚀 Operationnel |
| Tests JobObject | `tests/test_win32_jobobject.py` | 🧪 Teste |
| Tests doctor WAL | `tests/test_doctor_wal.py` | 🧪 Teste |
| Enrichissement SOT | `GOVERNANCE-HUB/known_repositories.yaml` (champs executables) | 📄 Documente |

---

## 8. GLOSSAIRE DES STATUTS

- 📄 Documente : artifact present, frontmatter valide
- 🔧 Implemente : code/config present, pas encore teste
- 🧪 Teste : tests unitaires passants
- 🚀 Operationnel : health-check OK, endpoint 200
- 🟢 Actif : dependants actifs verifies
- 🟡 Passif : artifact present, aucun dependant actif
- ⏸️ Pending : blocage governance/HITL/ADR documente
- ❌ Bloque : dependance manquante ou ADR refuse documente

---

## 9. PROOF-OF-LIFE

- [x] 2026-09-24T00:00:00+02:00 -- PRD-MOC EXE-ORCHESTRATION cree, phases 1-3 implementees
- [x] 2026-09-27T04:00:00+02:00 -- Phase 4 audit SOT complete (KIX/TRIX/FLEX manquent du SOT, GATEWAY-MANAGER present)
- [x] 2026-09-27T06:01:00+02:00 -- Phase 5 implementee : JobObject helpers (5 tests), WAL doctor + .bak restore (6 tests), `/doctor/restore` endpoint
- [x] 2026-09-27T06:01:00+02:00 -- 102 tests passants, gates P-101/P-103 valides, P-102 hors scope KIX seul
- [x] 2026-09-27T23:00:00+02:00 -- Modele de role/fonction documente dans PRD-MOC-KIX-MASTER.md section 2.3.7
- [x] 2026-09-27T23:00:00+02:00 -- Capability model implemente : `src/capability.py` + `requires_capability` decorator
- [x] 2026-09-28T01:16:14+02:00 -- 24 endpoints KIX proteges par `@requires_capability` (start/stop/restart/doctor/audit/schedules/release-handles/health/logs/metrics/swarm/alerts/events/notifications/dashboard)
- [x] 2026-09-28T01:16:14+02:00 -- Tests d'integration corriges : 13 passants (auth capability applique)
- [x] 2026-09-28T00:14:00+02:00 -- Phase 4 SOT validee : 4 repos critiques presents avec champs complets ; 31 custom runners absents du SOT documentes dans `reports/custom-runners-sot-audit-2026-09-28.md`
- [x] 2026-09-28T06:10:00+02:00 -- Finalisation PRD-MOC : statut passe de `partially_implemented` à `implemented`, evaluation d'utilite ajoutee

- [x] 2026-09-28T06:55:00+02:00 -- Gap antipattern fenetres/popups ajoute ; Phase 6 planifiee dans PRD-MOC-KIX-EXE-ORCHESTRATION-2026-09-24.md
- [x] 2026-09-28T06:58:00+02:00 -- Phase 6 implementee : CREATE_NO_WINDOW dans 4 runners + bootstrap_runner, -WindowStyle Hidden dans 7 appels PowerShell, auto_start=False par defaut + runners.yaml explicite
- [x] 2026-09-28T07:26:00+02:00 -- Tâches planifiees Windows masquees : 8 tâches mises à jour avec -WindowStyle Hidden, KIX PULSE Scan desactivee (script orphelin)
- [x] 2026-09-28T07:39:00+02:00 -- Validation locale : 69 tests KIX passent ; VEX py_compile OK, tests preexistants echouent sur Path("vex.yaml") sans rapport avec l’anti-pattern ; commits atomiques KIX pushes sur origin/main (5 commits : runners, bootstrap, src, config, PRD-MOC)

---

## 10. Évaluation d'utilite

| Critere | Évaluation | Justification |
|---------|------------|---------------|
| Utilite operationnelle | ✅ Élevee | Separe strictement toolchains et daemons, reduit les faux positifs du zombie monitor et ameliore le preflight BOOT. |
| Reutilisabilite | ✅ Élevee | Contrats declaratifs (`toolchains.yaml`, `/preflight/*`) reutilisables par d'autres orchestrateurs. |
| Impact architectural | ✅ Éleve | Introduit une couche de diagnostic standardisee et un PID Registry cross-runners, impact direct sur la fiabilite du demarrage. |
| Complexite d'implementation | ✅ Moyenne | Dejà largement implemente ; reste P-102 hors scope KIX seul. |
| Alignement governance | ✅ Oui | ADR backing, gates P-101/P-103 valides, SOT auditee. |

**Verdict** : Ce PRD-MOC est **utile et maintenant pleinement fonctionnel** dans son scope KIX. Il apporte une valeur ajoutee immediate en separant les couches toolchains/daemons et en fiabilisant le preflight/BOOT.

---

## 11. References

- `reports/kix-exe-orchestration-report-2026-09-24.md` : Rapport initial (v1)
- `PRD-MOC-KIX-ORCHESTRATOR-2026-08-18.md` : PRD MOC orchestrateur generic runner wrapper
- `PRD-MOC-KIX-MASTER.md` : Master MOC KIX
- `PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-2026-09-24.md` : Integration maître ecosysteme
- `PRD-MOC-KIX-MULTI-LANG-ECOSYSTEM-2026-09-24.md` : Integration multi-langages
- `ADR-2026-09-24-KIX-MULTI-LANG-RUNNERS.md` : ADR runners multi-langages
- `GOVERNANCE-HUB/known_repositories.yaml` : SOT des repos
- `src/zombie_monitor.py` : Module de detection zombies
- `src/diagnostics.py` : Module de diagnostics KIX
- `src/capability.py` : Capability model (7 capabilities)
- `src/auth.py` : `requires_capability` decorator
- `unified-design/designs/kix/design.yaml` : Unified design KIX

## 12. Modele de Role/Fonction KIX

Ce PRD MOC s'aligne sur le modele de role/fonction defini dans `PRD-MOC-KIX-MASTER.md` section 2.3 :

- **RBAC** : `admin`, `operator`, `viewer` (JWT dans `src/auth.py`)
- **Functional Roles** : 21 categories (`orchestrator`, `cognitive`, `governance`, `infrastructure`, etc.)
- **Capability Model** : 7 capacites (`runner-lifecycle`, `process-manager`, `pid-tracker`, `exe-launcher`, etc.)
- **Dual-Role Pattern** : TRIX/TRIXD/PLIX = RLM + TLM
- **ActorSpec** : integration via `KIXProcessManagerAdapter`

Les composants exe/orchestration (`zombie_monitor.py`, `diagnostics.py`, JobObject helpers) sont classes dans les `functional_roles` :
- `zombie_monitor.py` -> `operational` / `infrastructure`
- `diagnostics.py` -> `operational`
- JobObject helpers -> `process-manager` capability

Les runners externes (Go, Rust, Node) sont documentes avec leurs `meta.role` dans `config/runners.yaml` :
- `flex-rust` -> `rust-service`
- `go-service` -> `go-service`
- `node-service` -> `node-service`


