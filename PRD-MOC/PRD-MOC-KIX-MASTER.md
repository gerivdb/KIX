---
type: "PRD_MOC"
version: "1.0.0"
date: "2026-09-02"
updated: "2026-09-28"
status: "completed"
intent_hash: 0xPRD_MOC_KIX_MASTER_20260902
citizen: "L2-PLATFORM"
layer: "L2"
author: gerivdb
source_repo: gerivdb/KIX
source_path: MOC/PRD-MOC-KIX-MASTER.md
parent_doc: PRD-MOC-GOVERNANCE-HUB-MASTER.md
related_adr: ADR-2026-08-18-002-KIX-GENERIC-RUNNER-WRAPPER.md, ADR-2026-07-27-016-kix-orchestrator, ADR-2026-07-28-001-tlm-lang-runner, ADR-2026-08-10-001-single-global-github-token
related_intent: INTENT-Q243-NATIVE-INFERENCE-20260825
related_moc: PRD-MOC-GOVERNANCE-HUB-MASTER.md, PRD-MOC-GENERAL-MASTER.md, PRD-MOC-REPOS-MASTER.md, PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER-2026-09-27.md, PRD-MOC-KIX-MULTI-LANG-ECOSYSTEM-2026-09-24.md, PRD-MOC-KIX-EXE-ORCHESTRATION-2026-09-24.md, PRD-MOC-KIX-BOOTSTRAP-RUNNER-2026-08-20.md, PRD-MOC-VEX-KIX-BOUNDARIES-20260927.md, PRD-MOC-KIX-AGENT-MANAGER-20260928.md, PRD-MOC-KIX-ANAMORPHOSER-20260928.md, PRD-MOC-KIX-TLM-LANG-20260928.md
---

# PRD-MOC -- KIX Master : Orchestrateur Central RLM (L2-PLATFORM)

## Resume Executif

Ce MOC **MASTER** synthetise l'ensemble de la gouvernance **KIX (L2-PLATFORM)** : orchestrateur central du cycle de vie des runners RLM, API REST, registry declaratif, Doctor/Self-Healing, Swarm Status.

**Statut** : **completed** (2026-09-02) -- Implementation 100% fonctionnelle (Phases 1-5 terminees) + modele de role/fonction documente (dryrun causal 2026-09-27) + capability model implemente (2026-09-27) + 24 endpoints proteges (2026-09-28) + tests integration corriges (2026-09-28) + anti-pattern popups Windows corrige (Phase 6, 2026-09-28)

## 11. Subordonnes directs

| PRD-MOC | Role | Statut |
|---|---|
| PRD-MOC-KIX-ORCHESTRATOR-2026-08-18.md | Generic runner wrapper | completed |
| PRD-MOC-KIX-MULTI-LANG-ECOSYSTEM-2026-09-24.md | Multi-lang runners | implemented |
| PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER-2026-09-27.md | Écosysteme integration master | implemented |
| PRD-MOC-KIX-EXE-ORCHESTRATION-2026-09-24.md | Exe orchestration / preflight / zombie monitor | partially_implemented |
| PRD-MOC-KIX-BOOTSTRAP-RUNNER-2026-08-20.md | Bootstrap runner / amorçage ecosysteme | implemented |
| PRD-MOC-VEX-KIX-BOUNDARIES-20260927.md | Frontieres KIX/VEX | implemented |
| PRD-MOC-KIX-BATMCP-20260928.md | Integration BatMCP | implemented |
| PRD-MOC-KIX-ECOS-CLI-20260928.md | Integration ECOS-CLI | implemented |
| PRD-MOC-KIX-AGENT-MANAGER-20260928.md | Integration Agent Manager | implemented |
| PRD-MOC-KIX-ANAMORPHOSER-20260928.md | Integration Anamorphoser | implemented |
| PRD-MOC-KIX-TLM-LANG-20260928.md | Integration TLM-LANG | implemented |

---

## 1. Identite KIX

| Attribut | Valeur |
|---|---|
| **Nom** | KIX |
| **Repo** | gerivdb/KIX |
| **Chemin Local** | `D:\DO\WEB\TOOLS\L2-PLATFORM\KIX` |
| **Remote** | https://github.com/gerivdb/KIX |
| **Strate** | L2-PLATFORM |
| **Couches Logiques** | N1, N3 |
| **Port Principal** | 8800 |
| **Port TLM-LANG** | 8801 |
| **Statut** | active |
| **Intent Hash** | 0xKIX_ORCHESTRATOR_20260818 |
| **ADR Reference** | ADR-2026-08-18-002, ADR-2026-07-27-016 |

---

## 2. Architecture KIX

### 2.1 Role Principal

**KIX = Orchestrateur central du cycle de vie des runners RLM**

- Interface standard `RunnerBase` (start/stop/status/health/logs/restart)
- Registry declaratif `runners.yaml` -- zero logique de demarrage en dur
- API REST complete (start/stop/status/health/logs/restart)
- Doctor/Self-Healing integre (health checks parallelises)
- Swarm Status pour Agent Manager / N+2/N+3

### 2.2 Composants KIX (Implementes)

| Composant | Fichier | Statut | Description |
|---|---|---|---|
| **RunnerBase** | `runners/base.py` | ✅ **IMPLÉMENTÉ** | Interface `RunnerSpec`, `RunnerBase` (start/stop/status/health/logs/restart) |
| **Registry** | `runners/registry.py` | ✅ **IMPLÉMENTÉ** | `get_runner()`, `RUNNER_CLASSES`, chargement `runners.yaml` |
| **PythonRunner** | `runners/python_runner.py` | ✅ **IMPLÉMENTÉ** | Wrapper services Python (RLM-*, WAZAA, etc.) |
| **ZigRunner** | `runners/zig_runner.py` | ✅ **IMPLÉMENTÉ** | Wrapper binaires Zig (TRIX, LLUX, TIMX, ROOTX, TLM-LANG) |
| **GatewayRunner** | `runners/gateway_runner.py` | ✅ **IMPLÉMENTÉ** | Wrapper GATEWAY-MANAGER `.exe`/CLI |
| **RustRunner** | `runners/rust_runner.py` | ✅ **IMPLÉMENTÉ** | Wrapper services Rust (FLEX, TRIX, etc.) |
| **GoRunner** | `runners/go_runner.py` | ✅ **IMPLÉMENTÉ** | Wrapper services Go |
| **NodeRunner** | `runners/node_runner.py` | ✅ **IMPLÉMENTÉ** | Wrapper services Node.js |
| **CustomRunner** | `runners/custom_runner.py` | ✅ **IMPLÉMENTÉ** | Wrapper commande libre |
| **Registry declaratif** | `config/runners.yaml` | ✅ **IMPLÉMENTÉ** | 60 runners : python, zig-binary, gateway-exe, rust, go, node, custom |
| **API REST** | `src/app.py` | ✅ **IMPLÉMENTÉ** | `/runners`, `/doctor`, `/swarm/status`, `/runners/{name}/*` |
| **Doctor/Self-Healing** | `src/app.py` | ✅ **IMPLÉMENTÉ** | `/doctor` (verification), `/doctor/run` (auto-redemarrage) |
| **Swarm Status** | `src/app.py` | ✅ **IMPLÉMENTÉ** | `/swarm/status` -- etat agrege pour Agent Manager / N+2/N+3 |
| **Tests** | `tests/test_runners*.py` | ✅ **IMPLÉMENTÉ** | 52 tests passants (runners, integration, gateway, trixd, wazaa) |
| **Cleanup legacy** | `src/app.py` | ✅ **IMPLÉMENTÉ** | Supprime `_launch_runner()` legacy, `cognitive_runners.py` conservee |

### 2.3 Modele de Role/Fonction KIX

KIX implemente un modele de role/fonction à 5 dimensions, capture dans `unified-design/designs/kix/design.yaml` :

#### 2.3.1 RBAC API (authentification)

| Role | Permissions | Cas d'usage |
|------|-------------|-------------|
| `admin` | `runner:start/stop/restart`, `config:read/write`, `audit:read/write`, `remediation:trigger` | Gestion complete |
| `operator` | `runner:start/stop/status`, `logs:read` | Operations courantes |
| `viewer` | `runner:status`, `metrics:read`, `health:read` | Consultation seule |

Source : `src/auth.py` -- JWT avec `@login_required(roles=[...])`.

#### 2.3.2 Roles Fonctionnels Runners (`meta.role`)

21 categories fonctionnelles declarees dans `config/runners.yaml` :

| Role fonctionnel | Runners | Description |
|------------------|---------|-------------|
| `orchestrator` | kix, kix-ecosystem | Orchestration centrale |
| `bootstrap orchestrator` | bootstrap | Amorçage initial |
| `metrics collector` | rlm-metrics | Collecte metriques RLM |
| `configuration service` | rlm-config | Configuration centralisee |
| `deployment service` | rlm-deploy | Deploiement/release |
| `graph service` | rlm-graph | Service graphe |
| `security service` | rlm-secure | Securite/auth |
| `incident service` | rlm-incident | Gestion incidents |
| `release service` | rlm-release | Gestion releases |
| `knowledge-graph service` | kg-l | KG-L standalone |
| `decision-engine` | jevx | Moteur decision JEVX |
| `event-bus` | wazaa-bus | Bus evenementiels |
| `zig-runtime` | trixd | Runtime Zig dispatch |
| `governance` | gitex, repoxt, syncx, referex, kglx, harnex, nexus | Runners gouvernance |
| `cognitive` | talex, telox, timx, causex, etc. (18) | Runners cognitifs |
| `operational` | rlm243, timx-feature-store, rlm-mdu, piano, trix | Runners operationnels |
| `infrastructure` | flex, codedb-e5620, infx | Infrastructure |
| `llm` | llm-core | LLM core |
| `dashboard` | wazaa | Tableaux de bord |
| `api` | flex-api | APIs exposees |
| `citizen` | infx | Runners citoyens |

#### 2.3.3 Modele de Capacite

7 capacites operationnelles avec prerequis :

| Capacite | Required Capabilities | Service |
|----------|----------------------|---------|
| `runner-lifecycle` | runner:start/stop/restart | Cycle de vie complet |
| `tlm-runner` | runner:start, tlm:execute | TLM-LANG execution |
| `parallel-runner-manager` | runner:start/stop, concurrency:manage | Concurrency max 6 |
| `metrics-lifecycle` | metrics:read, runner:start | RLM-METRICS |
| `process-manager` | process:track/restart | Gestion processus |
| `pid-tracker` | pid:track, health:check | PID/fingerprint |
| `exe-launcher` | exe:launch | Chemins autorises |

#### 2.3.4 Dual-Role Pattern

Services appartenant à la fois aux familles **RLM** et **TLM** :

| Runner | Port | Familles |
|--------|------|----------|
| `trixd` | 7243 | RLM + TLM |
| `trix` | 0 | RLM + TLM |
| `plix` | 8788 | RLM + TLM |

Source : `service.py` -- `dual_role = port in SERVICE_MAP`.

#### 2.3.5 ActorSpec (base_orchestrator)

Modele externe `ActorSpec` (source : `base_orchestrator`) integre via `KIXProcessManagerAdapter` :

| Champ | Type | Mapping KIX |
|-------|------|-------------|
| `id` | str | `name` |
| `command` | str | `entrypoint` |
| `working_dir` | str | `working_dir` |
| `auto_restart` | bool | `auto_start` |
| `restart_delay` | int | 10s |
| `deployment` | dict | `meta.role`, `repo` |

#### 2.3.7 Implementation Capability Model (2026-09-27)

Le capability model defini dans `unified-design/designs/kix/design.yaml` est implemente dans le code KIX :

| Composant | Fichier | Statut |
|-----------|---------|--------|
| **Capability registry** | `src/capability.py` | ✅ Implemente |
| **Decorator `requires_capability`** | `src/auth.py` | ✅ Implemente |
| **Endpoints proteges par capability** | `src/app.py` | ✅ 11 endpoints mis à jour |
| **Tests capability** | `tests/test_capability.py` | ✅ 6 tests passants |

**Endpoints couverts par `requires_capability`** :

| Endpoint | Capability | RBAC |
|-----------|-----------|------|
| `POST /runners/{name}/start` | `runner:start` | admin/operator |
| `POST /runners/{name}/stop` | `runner:stop` | admin/operator |
| `POST /runners/{name}/restart` | `runner:restart` | admin/operator |
| `POST /doctor/run` | `remediation:trigger` | admin/operator |
| `POST /doctor/restore` | `remediation:trigger` | admin/operator |
| `GET /audit` | `audit:read` | admin |
| `GET /remediation/status` | `audit:read` | admin |
| `POST /schedule/cycle` | `runner:start` | admin/operator |
| `DELETE /schedule/cycle/{id}` | `config:write` | admin/operator |
| `GET /schedules` | `config:read` | admin/operator |
| `POST /process/release-handles` | `process:restart` | admin/operator |

### 2.4 Relation avec VEX (L3-CITIZENS)

**VEX** est l'orchestrateur L3 des daemons/agents autonomes. KIX et VEX partagent des concepts d'orchestration et de gestion de processus, mais leurs perimetres sont strictement separes :

- **KIX** : runners RLM (services applicatifs L2), alerting, auto-remediation, dashboard, auth, audit
- **VEX** : daemons L3, deploiement multi-OS (NSSM/schtasks/systemd), clients d'integration

Le contrat de frontieres est defini dans `PRD-MOC-VEX-KIX-BOUNDARIES-20260927.md`.

Points d'integration autorises :
- `GET /health/kix` -- VEX consulte le health de KIX
- `GET /health` -- KIX consulte le health agrege L3 de VEX
- WAZAA bus -- evenements daemons VEX et runners KIX

---

## 3. Configuration Declarative (`config/runners.yaml`)

```yaml
runners:
  - name: kix
    runner_type: python
    port: 8800
    working_dir: D:/DO/WEB/TOOLS/L2-PLATFORM/KIX
    entrypoint: src/app.py
    bootstrap: true
    health_path: /healthz
    restart_policy: always

  - name: gateway-manager
    runner_type: gateway-exe
    port: 8802
    working_dir: D:/DO/WEB/TOOLS/L1-INFRA/GATEWAY-MANAGER
    binary: gateway-manager.exe
    depends_on: [kix]
    restart_policy: always

  - name: trixd
    runner_type: zig-binary
    port: 8823
    working_dir: D:/DO/WEB/TOOLS/L4-TOOLS/TRIX
    binary: trix.exe
    depends_on: [kix]
    restart_policy: always

  - name: wazaa
    runner_type: python
    port: 1873
    working_dir: D:/DO/WEB/TOOLS/L4-TOOLS/WAZAA
    entrypoint: -m wazaa.wazaa_server
    depends_on: [kix]
    restart_policy: always

  - name: flex-api
    runner_type: python
    port: 7719
    working_dir: D:\DO\WEB\TOOLS\L4-TOOLS\FLEX
    entrypoint: flex_api.py
    depends_on: [kix]
    restart_policy: always
```

---

## 4. Endpoints API KIX

| Endpoint | Methode | Description |
|---|---|---|
| `/runners` | GET | Liste tous les runners avec status |
| `/runners/{name}/start` | POST | Demarre un runner |
| `/runners/{name}/stop` | POST | Arrete un runner |
| `/runners/{name}/status` | GET | Status d'un runner |
| `/runners/{name}/health` | GET | Health-check d'un runner |
| `/runners/{name}/logs` | GET | Logs d'un runner |
| `/runners/{name}/restart` | POST | Redemarre un runner |
| `/health` | GET | Health-check global KIX |
| `/healthz` | GET | Liveness probe |
| `/readyz` | GET | Readiness probe (dependances) |
| `/doctor` | GET | Verifie tous les runners, retourne erreurs |
| `/doctor/run` | POST | Redemarre les runners en erreur |
| `/swarm/status` | GET | État agrege pour Agent Manager / N+2/N+3 |

---

## 5. Gates KIX (MOX)

| Gate | Critere | Statut |
|---|---|---|
| **P-108** | ADR accepted par tous les leads (KIX, GATEWAY-MANAGER, WAZAA, TRIX) | ✅ **VALIDÉ** |
| **P-109** | Phase 1 implementee et testee (52 tests passants) | ✅ **VALIDÉ** |
| **P-110** | BUZZ-X fonctionnel avant integration dans KIX | ❌ **BLOQUÉ** (BUZZ-X non fonctionnel) |

---

## 6. Dependances KIX

| Dependance | Localisation | Usage | Statut |
|---|---|---|---|
| `src/app.py` | `D:\DO\WEB\TOOLS\L2-PLATFORM\KIX\src\app.py` | API REST existante | ✅ Disponible |
| `cognitive_runners.py` | `src\cognitive_runners.py` | Registry runners Python (legacy) | ✅ Conserve |
| `runner_state.py` | `src\runner_state.py` | Store SQLite | ✅ Disponible |
| `zombie_monitor.py` | `src\zombie_monitor.py` | Detection zombies | ✅ Disponible |
| `runners/base.py` | `runners\base.py` | Interface `RunnerSpec`, `RunnerBase` | ✅ IMPLÉMENTÉ |
| `runners/registry.py` | `runners\registry.py` | Registry generique | ✅ IMPLÉMENTÉ |
| `runners/python_runner.py` | `runners\python_runner.py` | Wrapper Python | ✅ IMPLÉMENTÉ |
| `runners/zig_runner.py` | `runners\zig_runner.py` | Wrapper Zig | ✅ IMPLÉMENTÉ |
| `runners/gateway_runner.py` | `runners\gateway_runner.py` | Wrapper Gateway-MANAGER | ✅ IMPLÉMENTÉ |
| `config/runners.yaml` | `config\runners.yaml` | Registry declaratif | ✅ IMPLÉMENTÉ |

---

## 7. Runners Geres par KIX (via `runners.yaml`)

| Runner | Type | Port | Dependances | Bootstrap | Restart Policy |
|---|---|---|---|---|---|
| **kix** | python | 8800 | -- | true | always |
| **bootstrap** | python | 8810 | [kix, gateway-manager, trixd, wazaa, flex-api] | true | on-failure |
| **gateway-manager** | gateway-exe | 8802 | [kix] | false | always |
| **trixd** | zig-binary | 8823 | [kix] | false | always |
| **wazaa** | python | 1873 | [kix] | false | always |
| **flex-api** | python | 7719 | [kix] | false | always |

> **Note** : TLM-LANG (port 8801) est archive -- runner KIX pour langage TLM non utilise actuellement.
> **Note** : `gateway-manager` n'a plus `bootstrap: true` depuis ADR-2026-08-20-001. Le role bootstrap est assume par le runner dedie `bootstrap` (port 8810).

---

## 8. Subalternes KIX (RLM Runners)

KIX gere 17 runners cognitifs Python (legacy `cognitive_runners.py`) en cours de migration vers `runners.yaml` :

| Runner | Type | Port | Description |
|---|---|---|---|
| RLM-RELEASE | python | 8803 | Release management |
| RLM-SECURE | python | 8804 | Security scanning |
| RLM-METRICS | python | 8805 | Metrics collection |
| RLM-INCIDENT | python | 8806 | Incident management |
| RLM-DEPLOY | python | 8807 | Deployment |
| RLM-CONFIG | python | 8808 | Configuration management |
| RLM-GRAPH | python | 8809 | Graph operations |
| RLM-RELEASE | python | 8803 | Release management |
| RLM-MDU | python | 8810 | MDU operations |
| RLM-INCIDENT | python | 8806 | Incident management |
| RLM-SECURE | python | 8804 | Security |
| RLM-CONFIG | python | 8808 | Configuration |
| RLM-GRAPH | python | 8809 | Graph |
| RLM-METRICS | python | 8805 | Metrics |
| RLM-RELEASE | python | 8803 | Release |
| RLM-SECURE | python | 8804 | Security |
| RLM-CONFIG | python | 8808 | Config |

> **Note** : Migration progressive vers `runners.yaml` en cours (Phase 5 cleanup).

---

## 8. Subalternes Externes (KIX gere via runners.yaml)

| Service | Repo | Port | Type | Statut |
|---|---|---|---|---|
| **GATEWAY-MANAGER** | gerivdb/GATEWAY-MANAGER | 8802 | gateway-exe | ✅ Gere |
| **TRIX** | gerivdb/TRIX | 8823 | zig-binary | ✅ Gere |
| **WAZAA** | gerivdb/WAZAA | 1873 | python | ✅ Gere |
| **FLEX-API (FLEX-L4)** | gerivdb/FLEX | 7719 | python | ✅ Gere |
| **TLM-LANG** | gerivdb/TLM-LANG | 8801 | python | ❌ Archived |

---

## 9. Cross-Repo Dependencies

| Source | Cible | Type | Protocole |
|---|---|---|---|
| KIX -> GATEWAY-MANAGER | Orchestration -> Proxy/Clapet | gateway-exe | REST + WAZAA |
| KIX -> TRIX | Orchestration -> Runtime Zig | zig-binary | REST + WAZAA |
| KIX -> WAZAA | Orchestration -> Bus evenementiel | python | WAZAA Bus |
| KIX -> FLEX | Orchestration -> Cache/Flex | python | REST + WAZAA |
| KIX -> TLM-LANG | Orchestration -> Runner TLM | python | REST (archived) |

---

## 10. Points d'Entree Operationnels KIX

| Operation | Commande | Description |
|---|---|---|
| **Demarrage KIX** | `python src/app.py` | Demarre API sur 8800 |
| **Health Check** | `curl http://localhost:8800/healthz` | Liveness probe |
| **Readiness** | `curl http://localhost:8800/readyz` | Readiness probe |
| **Liste Runners** | `curl http://localhost:8800/runners` | Liste tous les runners |
| **Doctor Check** | `curl http://localhost:8800/doctor` | Verification complete |
| **Auto-Heal** | `curl -X POST http://localhost:8800/doctor/run` | Auto-restart runners KO |
| **Swarm Status** | `curl http://localhost:8800/swarm/status` | État pour Agent Manager |
| **Runner Logs** | `curl http://localhost:8800/runners/{name}/logs` | Logs d'un runner |
| **Bootstrap Status** | `curl http://localhost:8810/bootstrap/status` | Status detaille bootstrap |
| **Bootstrap Ready** | `curl http://localhost:8810/bootstrap/ready` | Ready global ecosysteme |
| **Bootstrap Monitor** | `curl http://localhost:8810/bootstrap/monitor` | Monitoring alertes bootstrap |

---

## 11. Gouvernance KIX

### 10.1 Regles d'Acceptation
- [x] Review par Lead KIX
- [x] Review par Lead GATEWAY-MANAGER
- [x] Review par Lead WAZAA
- [x] Review par Lead TRIX
- [x] Validation ADR par Team DevTools Architecture
- [x] Tests d'integration Phase 1 passants (52 tests)

### 10.2 Enforcement Mode
```yaml
enforcement_mode:
  ci: hooks-only
  branch_protection: status-checks-only
  hooks: minimal
  rss_lint: profile-only
  vyoa: commit-only
  brgs: none
```

---

## 11. Points d'Attention / Risques

| Risque | Impact | Probabilite | Mitigation |
|---|---|---|---|
| Bootstrap circulaire (KIX s'orchestre lui-meme) | HIGH | MOYENNE | `bootstrap: true` explicite + `bootstrap.sh` externe |
| Migration `cognitive_runners.py` cassee | HIGH | FAIBLE | Phase 1 garde le code legacy, migration progressive |
| Doctor faux negatifs (timeout trop court) | LOW | MOYENNE | Timeout configurable + logs detailles |
| BUZZ-X non fonctionnel (Phase 4 bloquee) | MEDIUM | CERTAINE | Exclu de la portee initiale |
| Divergence meta.role YAML vs functional_roles design | LOW | FAIBLE | Documente dans section 2.3.6 ; vue agregee vs vue technique |
| Capability model non couvert sur tous les endpoints | LOW | FAIBLE | 11/41 endpoints couverts ; reste à etendre aux endpoints lecture seule (metrics, health, logs) |

---

## 12. Preuves & References

| Preuve | Description |
|---|---|
| `PRD-MOC-KIX-ORCHESTRATOR-2026-08-18.md` | PRD MOC principal KIX (IMPLEMENTED) |
| `config/runners.yaml` | Registry declaratif 5 runners |
| `tests/test_runners*.py` | 52 tests passants |
| `src/app.py` | API REST complete |
| `runners/*.py` | 4 wrappers implementes |
| `src/capability.py` | Capability model (7 capabilities) |
| `src/auth.py` | `requires_capability` decorator |
| `tests/test_capability.py` | 6 tests capability model passants |

---

## 13. References Croisees

| Type | Reference |
|---|---|
| **ADR Principal** | ADR-2026-08-18-002-KIX-GENERIC-RUNNER-WRAPPER.md |
| **ADR Orchestrator** | ADR-2026-07-27-016-kix-orchestrator |
| **ADR TLM-LANG** | ADR-2026-07-28-001-tlm-lang-runner |
| **ADR Token** | ADR-2026-08-10-001-single-global-github-token |
| **MOC Parent** | PRD-MOC-GOVERNANCE-HUB-MASTER.md |
| **MOC General** | PRD-MOC-GENERAL-MASTER.md (GEN-030e, GEN-031-L6) |
| **MOC Repos** | PRD-MOC-REPOS-MASTER.md (repos/kix.md) |
| **Intent** | INTENT-Q243-NATIVE-INFERENCE-20260825 |
| **PRD MOC Bootstrap** | PRD-MOC-KIX-BOOTSTRAP-RUNNER-2026-08-20.md |
| **PRD MOC Boundaries** | PRD-MOC-VEX-KIX-BOUNDARIES-20260927.md |

---

## Évaluation d'utilite des PRD MOC KIX

| PRD MOC | Utilite | Justification |
|---------|---------|---------------|
| `PRD-MOC-KIX-MASTER.md` | ✅ Essentiel | Vue d'ensemble consolidee de la gouvernance KIX. Reference unique pour les subalternes et les cross-repos. |
| `PRD-MOC-KIX-ORCHESTRATOR-2026-08-18.md` | ✅ Essentiel | Specifie le generic runner wrapper, base de tous les runners. ADR backing. |
| `PRD-MOC-KIX-MULTI-LANG-ECOSYSTEM-2026-09-24.md` | ✅ Utile | Formalise l'extension Rust/Go/Node et la gestion des processus systeme. Couverture multi-langage. |
| `PRD-MOC-KIX-EXE-ORCHESTRATION-2026-09-24.md` | ✅ Utile | Couvre toolchains, preflight, zombie monitor, doctor WAL. Reduit les faux positifs d'orchestration. |
| `PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-2026-09-24.md` | ⚠️ Remplace | `superseded` par `PRD-MOC-KIX-MULTI-LANG-ECOSYSTEM-2026-09-24.md`. À archiver, pas de valeur ajoutee active. |
| `PRD-MOC-KIX-BOOTSTRAP-RUNNER-2026-08-20.md` | ✅ Essentiel | Formalise le runner d'amorçage, separe de gateway-manager. Endpoints `/bootstrap/*`, ECOS CLI, watchdog. ADR backing. |
| `PRD-MOC-KIX-VEX-KIX-BOUNDARIES-20260927.md` | ✅ Essentiel | Contrat de frontieres KIX/VEX. Points d'integration autorises, interdits, WAZAA bus, bootstrap coordination. |
| `PRD-MOC-KIX-BATMCP-20260928.md` | ✅ Utile | Formalise l'integration BatMCP comme runner gateway-exe. Health checks, capability model, preuves d'execution. |
| `PRD-MOC-KIX-ECOS-CLI-20260928.md` | ✅ Utile | Formalise l'integration ECOS-CLI comme runner gateway-exe. BDCP, PAT rotation, bootstrap coordination. |

**Recommandation** : conserver les PRD MOC `MASTER`, `ORCHESTRATOR`, `MULTI-LANG`, `EXE-ORCHESTRATION`, `BOOTSTRAP-RUNNER`, `VEX-KIX-BOUNDARIES`, `BATMCP`, `ECOS-CLI`. Supprimer ou archiver `ECOSYSTEM-INTEGRATION` (remplace).

### Mise à jour 2026-09-27 -- Modele de Role/Fonction

| Document | Mise à jour | Description |
|----------|-------------|-------------|
| `unified-design/designs/kix/design.yaml` | ✅ Ajout sections `roles`, `functional_roles`, `capability_model`, `dual_role_pattern`, `actor_model`, `adr_refs` | Modele de role/fonction complet, 60 runners couverts, 21 categories fonctionnelles |
| `unified-design/designs/kix-error-recovery/design.yaml` | ✅ Description enrichie | Reference au modele de role/fonction KIX pour remediation triggers |
| `config/runners.yaml` | ✅ Ajout `meta.role` manquants | 5 runners completes : friction-analyzer, agent-manager, nodex, rootx, kg-l-coherence-watchdog |
| `PRD-MOC-KIX-MASTER.md` | ✅ Section 2.3 + 2.3.6 + 2.3.7 | Documentation du modele de role/fonction + constats dryrun causal + implementation capability model |
| `PRD-MOC-KIX-ORCHESTRATOR-2026-08-18.md` | ✅ Section 4.4 | Documentation du modele de role/fonction |
| `PRD-MOC-KIX-MULTI-LANG-ECOSYSTEM-2026-09-24.md` | ✅ Section 9 | Documentation du modele de role/fonction pour runners Rust/Go/Node |
| `PRD-MOC-KIX-EXE-ORCHESTRATION-2026-09-24.md` | ✅ Section 11 | Documentation du modele de role/fonction pour exe/orchestration |
| `PRD-MOC-VEX-KIX-BOUNDARIES-20260927.md` | ✅ Section 14 | Documentation du modele de role/fonction pour les frontieres KIX/VEX |
| `src/capability.py` | ✅ Nouveau fichier | Capability registry (7 capabilities) |
| `src/auth.py` | ✅ `requires_capability` decorator | Verification capability dans les endpoints |
| `src/app.py` | ✅ 11 endpoints mis à jour | `@requires_capability` sur start/stop/restart/doctor/audit/schedules/release-handles |
| `tests/test_capability.py` | ✅ Nouveau fichier | 6 tests passants pour capability model |

**IntentHash** : 0xPRD_MOC_KIX_MASTER_20260902  
**Status** : completed  
**Date** : 2026-09-02  
**Derniere mise à jour** : 2026-09-27
