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
related_moc: PRD-MOC-GOVERNANCE-HUB-MASTER.md, PRD-MOC-GENERAL-MASTER.md, PRD-MOC-REPOS-MASTER.md, PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER-2026-09-27.md, PRD-MOC-KIX-MULTI-LANG-ECOSYSTEM-2026-09-24.md, PRD-MOC-KIX-EXE-ORCHESTRATION-2026-09-24.md, PRD-MOC-KIX-BOOTSTRAP-RUNNER-2026-08-20.md, PRD-MOC-VEX-KIX-BOUNDARIES-20260927.md
---

# PRD-MOC — KIX Master : Orchestrateur Central RLM (L2-PLATFORM)

## Résumé Exécutif

Ce MOC **MASTER** synthétise l'ensemble de la gouvernance **KIX (L2-PLATFORM)** : orchestrateur central du cycle de vie des runners RLM, API REST, registry déclaratif, Doctor/Self-Healing, Swarm Status.

**Statut** : **completed** (2026-09-02) — Implémentation 100% fonctionnelle (Phases 1-5 terminées) + modèle de rôle/fonction documenté (dryrun causal 2026-09-27) + capability model implémenté (2026-09-27) + 24 endpoints protégés (2026-09-28) + tests intégration corrigés (2026-09-28)

## 11. Subordonnés directs

| PRD-MOC | Rôle | Statut |
|---|---|
| PRD-MOC-KIX-ORCHESTRATOR-2026-08-18.md | Generic runner wrapper | completed |
| PRD-MOC-KIX-MULTI-LANG-ECOSYSTEM-2026-09-24.md | Multi-lang runners | implemented |
| PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER-2026-09-27.md | Écosystème integration master | implemented |
| PRD-MOC-KIX-EXE-ORCHESTRATION-2026-09-24.md | Exe orchestration / preflight / zombie monitor | partially_implemented |
| PRD-MOC-KIX-BOOTSTRAP-RUNNER-2026-08-20.md | Bootstrap runner / amorçage écosystème | implemented |
| PRD-MOC-VEX-KIX-BOUNDARIES-20260927.md | Frontières KIX/VEX | implemented |
| PRD-MOC-KIX-BATMCP-20260928.md | Intégration BatMCP | implemented |
| PRD-MOC-KIX-ECOS-CLI-20260928.md | Intégration ECOS-CLI | implemented |

---

## 1. Identité KIX

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
| **ADR Référence** | ADR-2026-08-18-002, ADR-2026-07-27-016 |

---

## 2. Architecture KIX

### 2.1 Rôle Principal

**KIX = Orchestrateur central du cycle de vie des runners RLM**

- Interface standard `RunnerBase` (start/stop/status/health/logs/restart)
- Registry déclaratif `runners.yaml` — zéro logique de démarrage en dur
- API REST complète (start/stop/status/health/logs/restart)
- Doctor/Self-Healing intégré (health checks parallélisés)
- Swarm Status pour Agent Manager / N+2/N+3

### 2.2 Composants KIX (Implémentés)

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
| **Registry déclaratif** | `config/runners.yaml` | ✅ **IMPLÉMENTÉ** | 60 runners : python, zig-binary, gateway-exe, rust, go, node, custom |
| **API REST** | `src/app.py` | ✅ **IMPLÉMENTÉ** | `/runners`, `/doctor`, `/swarm/status`, `/runners/{name}/*` |
| **Doctor/Self-Healing** | `src/app.py` | ✅ **IMPLÉMENTÉ** | `/doctor` (vérification), `/doctor/run` (auto-redémarrage) |
| **Swarm Status** | `src/app.py` | ✅ **IMPLÉMENTÉ** | `/swarm/status` — état agrégé pour Agent Manager / N+2/N+3 |
| **Tests** | `tests/test_runners*.py` | ✅ **IMPLÉMENTÉ** | 52 tests passants (runners, intégration, gateway, trixd, wazaa) |
| **Cleanup legacy** | `src/app.py` | ✅ **IMPLÉMENTÉ** | Supprimé `_launch_runner()` legacy, `cognitive_runners.py` conservée |

### 2.3 Modèle de Rôle/Fonction KIX

KIX implémente un modèle de rôle/fonction à 5 dimensions, capturé dans `unified-design/designs/kix/design.yaml` :

#### 2.3.1 RBAC API (authentification)

| Rôle | Permissions | Cas d'usage |
|------|-------------|-------------|
| `admin` | `runner:start/stop/restart`, `config:read/write`, `audit:read/write`, `remediation:trigger` | Gestion complète |
| `operator` | `runner:start/stop/status`, `logs:read` | Opérations courantes |
| `viewer` | `runner:status`, `metrics:read`, `health:read` | Consultation seule |

Source : `src/auth.py` — JWT avec `@login_required(roles=[...])`.

#### 2.3.2 Rôles Fonctionnels Runners (`meta.role`)

21 catégories fonctionnelles déclarées dans `config/runners.yaml` :

| Rôle fonctionnel | Runners | Description |
|------------------|---------|-------------|
| `orchestrator` | kix, kix-ecosystem | Orchestration centrale |
| `bootstrap orchestrator` | bootstrap | Amorçage initial |
| `metrics collector` | rlm-metrics | Collecte métriques RLM |
| `configuration service` | rlm-config | Configuration centralisée |
| `deployment service` | rlm-deploy | Déploiement/release |
| `graph service` | rlm-graph | Service graphe |
| `security service` | rlm-secure | Sécurité/auth |
| `incident service` | rlm-incident | Gestion incidents |
| `release service` | rlm-release | Gestion releases |
| `knowledge-graph service` | kg-l | KG-L standalone |
| `decision-engine` | jevx | Moteur décision JEVX |
| `event-bus` | wazaa-bus | Bus événementiels |
| `zig-runtime` | trixd | Runtime Zig dispatch |
| `governance` | gitex, repoxt, syncx, referex, kglx, harnex, nexus | Runners gouvernance |
| `cognitive` | talex, telox, timx, causex, etc. (18) | Runners cognitifs |
| `operational` | rlm243, timx-feature-store, rlm-mdu, piano, trix | Runners opérationnels |
| `infrastructure` | flex, codedb-e5620, infx | Infrastructure |
| `llm` | llm-core | LLM core |
| `dashboard` | wazaa | Tableaux de bord |
| `api` | flex-api | APIs exposées |
| `citizen` | infx | Runners citoyens |

#### 2.3.3 Modèle de Capacité

7 capacités opérationnelles avec prérequis :

| Capacité | Required Capabilities | Service |
|----------|----------------------|---------|
| `runner-lifecycle` | runner:start/stop/restart | Cycle de vie complet |
| `tlm-runner` | runner:start, tlm:execute | TLM-LANG execution |
| `parallel-runner-manager` | runner:start/stop, concurrency:manage | Concurrency max 6 |
| `metrics-lifecycle` | metrics:read, runner:start | RLM-METRICS |
| `process-manager` | process:track/restart | Gestion processus |
| `pid-tracker` | pid:track, health:check | PID/fingerprint |
| `exe-launcher` | exe:launch | Chemins autorisés |

#### 2.3.4 Dual-Role Pattern

Services appartenant à la fois aux familles **RLM** et **TLM** :

| Runner | Port | Familles |
|--------|------|----------|
| `trixd` | 7243 | RLM + TLM |
| `trix` | 0 | RLM + TLM |
| `plix` | 8788 | RLM + TLM |

Source : `service.py` — `dual_role = port in SERVICE_MAP`.

#### 2.3.5 ActorSpec (base_orchestrator)

Modèle externe `ActorSpec` (source : `base_orchestrator`) intégré via `KIXProcessManagerAdapter` :

| Champ | Type | Mapping KIX |
|-------|------|-------------|
| `id` | str | `name` |
| `command` | str | `entrypoint` |
| `working_dir` | str | `working_dir` |
| `auto_restart` | bool | `auto_start` |
| `restart_delay` | int | 10s |
| `deployment` | dict | `meta.role`, `repo` |

#### 2.3.7 Implémentation Capability Model (2026-09-27)

Le capability model défini dans `unified-design/designs/kix/design.yaml` est implémenté dans le code KIX :

| Composant | Fichier | Statut |
|-----------|---------|--------|
| **Capability registry** | `src/capability.py` | ✅ Implémenté |
| **Decorator `requires_capability`** | `src/auth.py` | ✅ Implémenté |
| **Endpoints protégés par capability** | `src/app.py` | ✅ 11 endpoints mis à jour |
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

**VEX** est l'orchestrateur L3 des daemons/agents autonomes. KIX et VEX partagent des concepts d'orchestration et de gestion de processus, mais leurs périmètres sont strictement séparés :

- **KIX** : runners RLM (services applicatifs L2), alerting, auto-remédiation, dashboard, auth, audit
- **VEX** : daemons L3, déploiement multi-OS (NSSM/schtasks/systemd), clients d'intégration

Le contrat de frontières est défini dans `PRD-MOC-VEX-KIX-BOUNDARIES-20260927.md`.

Points d'intégration autorisés :
- `GET /health/kix` — VEX consulte le health de KIX
- `GET /health` — KIX consulte le health agrégé L3 de VEX
- WAZAA bus — événements daemons VEX et runners KIX

---

## 3. Configuration Déclarative (`config/runners.yaml`)

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

| Endpoint | Méthode | Description |
|---|---|---|
| `/runners` | GET | Liste tous les runners avec status |
| `/runners/{name}/start` | POST | Démarre un runner |
| `/runners/{name}/stop` | POST | Arrête un runner |
| `/runners/{name}/status` | GET | Status d'un runner |
| `/runners/{name}/health` | GET | Health-check d'un runner |
| `/runners/{name}/logs` | GET | Logs d'un runner |
| `/runners/{name}/restart` | POST | Redémarre un runner |
| `/health` | GET | Health-check global KIX |
| `/healthz` | GET | Liveness probe |
| `/readyz` | GET | Readiness probe (dépendances) |
| `/doctor` | GET | Vérifie tous les runners, retourne erreurs |
| `/doctor/run` | POST | Redémarre les runners en erreur |
| `/swarm/status` | GET | État agrégé pour Agent Manager / N+2/N+3 |

---

## 5. Gates KIX (MOX)

| Gate | Critère | Statut |
|---|---|---|
| **P-108** | ADR accepted par tous les leads (KIX, GATEWAY-MANAGER, WAZAA, TRIX) | ✅ **VALIDÉ** |
| **P-109** | Phase 1 implémentée et testée (52 tests passants) | ✅ **VALIDÉ** |
| **P-110** | BUZZ-X fonctionnel avant intégration dans KIX | ❌ **BLOQUÉ** (BUZZ-X non fonctionnel) |

---

## 6. Dépendances KIX

| Dépendance | Localisation | Usage | Statut |
|---|---|---|---|
| `src/app.py` | `D:\DO\WEB\TOOLS\L2-PLATFORM\KIX\src\app.py` | API REST existante | ✅ Disponible |
| `cognitive_runners.py` | `src\cognitive_runners.py` | Registry runners Python (legacy) | ✅ Conservé |
| `runner_state.py` | `src\runner_state.py` | Store SQLite | ✅ Disponible |
| `zombie_monitor.py` | `src\zombie_monitor.py` | Détection zombies | ✅ Disponible |
| `runners/base.py` | `runners\base.py` | Interface `RunnerSpec`, `RunnerBase` | ✅ IMPLÉMENTÉ |
| `runners/registry.py` | `runners\registry.py` | Registry générique | ✅ IMPLÉMENTÉ |
| `runners/python_runner.py` | `runners\python_runner.py` | Wrapper Python | ✅ IMPLÉMENTÉ |
| `runners/zig_runner.py` | `runners\zig_runner.py` | Wrapper Zig | ✅ IMPLÉMENTÉ |
| `runners/gateway_runner.py` | `runners\gateway_runner.py` | Wrapper Gateway-MANAGER | ✅ IMPLÉMENTÉ |
| `config/runners.yaml` | `config\runners.yaml` | Registry déclaratif | ✅ IMPLÉMENTÉ |

---

## 7. Runners Gérés par KIX (via `runners.yaml`)

| Runner | Type | Port | Dépendances | Bootstrap | Restart Policy |
|---|---|---|---|---|---|
| **kix** | python | 8800 | — | true | always |
| **bootstrap** | python | 8810 | [kix, gateway-manager, trixd, wazaa, flex-api] | true | on-failure |
| **gateway-manager** | gateway-exe | 8802 | [kix] | false | always |
| **trixd** | zig-binary | 8823 | [kix] | false | always |
| **wazaa** | python | 1873 | [kix] | false | always |
| **flex-api** | python | 7719 | [kix] | false | always |

> **Note** : TLM-LANG (port 8801) est archivé — runner KIX pour langage TLM non utilisé actuellement.
> **Note** : `gateway-manager` n'a plus `bootstrap: true` depuis ADR-2026-08-20-001. Le rôle bootstrap est assumé par le runner dédié `bootstrap` (port 8810).

---

## 8. Subalternes KIX (RLM Runners)

KIX gère 17 runners cognitifs Python (legacy `cognitive_runners.py`) en cours de migration vers `runners.yaml` :

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

## 8. Subalternes Externes (KIX gère via runners.yaml)

| Service | Repo | Port | Type | Statut |
|---|---|---|---|---|
| **GATEWAY-MANAGER** | gerivdb/GATEWAY-MANAGER | 8802 | gateway-exe | ✅ Géré |
| **TRIX** | gerivdb/TRIX | 8823 | zig-binary | ✅ Géré |
| **WAZAA** | gerivdb/WAZAA | 1873 | python | ✅ Géré |
| **FLEX-API (FLEX-L4)** | gerivdb/FLEX | 7719 | python | ✅ Géré |
| **TLM-LANG** | gerivdb/TLM-LANG | 8801 | python | ❌ Archived |

---

## 9. Cross-Repo Dependencies

| Source | Cible | Type | Protocole |
|---|---|---|---|
| KIX → GATEWAY-MANAGER | Orchestration → Proxy/Clapet | gateway-exe | REST + WAZAA |
| KIX → TRIX | Orchestration → Runtime Zig | zig-binary | REST + WAZAA |
| KIX → WAZAA | Orchestration → Bus événementiel | python | WAZAA Bus |
| KIX → FLEX | Orchestration → Cache/Flex | python | REST + WAZAA |
| KIX → TLM-LANG | Orchestration → Runner TLM | python | REST (archived) |

---

## 10. Points d'Entrée Opérationnels KIX

| Opération | Commande | Description |
|---|---|---|
| **Démarrage KIX** | `python src/app.py` | Démarre API sur 8800 |
| **Health Check** | `curl http://localhost:8800/healthz` | Liveness probe |
| **Readiness** | `curl http://localhost:8800/readyz` | Readiness probe |
| **Liste Runners** | `curl http://localhost:8800/runners` | Liste tous les runners |
| **Doctor Check** | `curl http://localhost:8800/doctor` | Vérification complète |
| **Auto-Heal** | `curl -X POST http://localhost:8800/doctor/run` | Auto-restart runners KO |
| **Swarm Status** | `curl http://localhost:8800/swarm/status` | État pour Agent Manager |
| **Runner Logs** | `curl http://localhost:8800/runners/{name}/logs` | Logs d'un runner |
| **Bootstrap Status** | `curl http://localhost:8810/bootstrap/status` | Status détaillé bootstrap |
| **Bootstrap Ready** | `curl http://localhost:8810/bootstrap/ready` | Ready global écosystème |
| **Bootstrap Monitor** | `curl http://localhost:8810/bootstrap/monitor` | Monitoring alertes bootstrap |

---

## 11. Gouvernance KIX

### 10.1 Règles d'Acceptation
- [x] Review par Lead KIX
- [x] Review par Lead GATEWAY-MANAGER
- [x] Review par Lead WAZAA
- [x] Review par Lead TRIX
- [x] Validation ADR par Team DevTools Architecture
- [x] Tests d'intégration Phase 1 passants (52 tests)

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

| Risque | Impact | Probabilité | Mitigation |
|---|---|---|---|
| Bootstrap circulaire (KIX s'orchestre lui-même) | HIGH | MOYENNE | `bootstrap: true` explicite + `bootstrap.sh` externe |
| Migration `cognitive_runners.py` cassée | HIGH | FAIBLE | Phase 1 garde le code legacy, migration progressive |
| Doctor faux négatifs (timeout trop court) | LOW | MOYENNE | Timeout configurable + logs détaillés |
| BUZZ-X non fonctionnel (Phase 4 bloquée) | MEDIUM | CERTAINE | Exclu de la portée initiale |
| Divergence meta.role YAML vs functional_roles design | LOW | FAIBLE | Documenté dans section 2.3.6 ; vue agrégée vs vue technique |
| Capability model non couvert sur tous les endpoints | LOW | FAIBLE | 11/41 endpoints couverts ; reste à étendre aux endpoints lecture seule (metrics, health, logs) |

---

## 12. Preuves & Références

| Preuve | Description |
|---|---|
| `PRD-MOC-KIX-ORCHESTRATOR-2026-08-18.md` | PRD MOC principal KIX (IMPLEMENTED) |
| `config/runners.yaml` | Registry déclaratif 5 runners |
| `tests/test_runners*.py` | 52 tests passants |
| `src/app.py` | API REST complète |
| `runners/*.py` | 4 wrappers implémentés |
| `src/capability.py` | Capability model (7 capabilities) |
| `src/auth.py` | `requires_capability` decorator |
| `tests/test_capability.py` | 6 tests capability model passants |

---

## 13. Références Croisées

| Type | Référence |
|---|---|
| **ADR Principal** | ADR-2026-08-18-002-KIX-GENERIC-RUNNER-WRAPPER.md |
| **ADR Orchestrator** | ADR-2026-07-27-016-kix-orchestrator |
| **ADR TLM-LANG** | ADR-2026-07-28-001-tlm-lang-runner |
| **ADR Token** | ADR-2026-08-10-001-single-global-github-token |
| **MOC Parent** | PRD-MOC-GOVERNANCE-HUB-MASTER.md |
| **MOC Général** | PRD-MOC-GENERAL-MASTER.md (GEN-030e, GEN-031-L6) |
| **MOC Repos** | PRD-MOC-REPOS-MASTER.md (repos/kix.md) |
| **Intent** | INTENT-Q243-NATIVE-INFERENCE-20260825 |
| **PRD MOC Bootstrap** | PRD-MOC-KIX-BOOTSTRAP-RUNNER-2026-08-20.md |
| **PRD MOC Boundaries** | PRD-MOC-VEX-KIX-BOUNDARIES-20260927.md |

---

## Évaluation d'utilité des PRD MOC KIX

| PRD MOC | Utilité | Justification |
|---------|---------|---------------|
| `PRD-MOC-KIX-MASTER.md` | ✅ Essentiel | Vue d'ensemble consolidée de la gouvernance KIX. Référence unique pour les subalternes et les cross-repos. |
| `PRD-MOC-KIX-ORCHESTRATOR-2026-08-18.md` | ✅ Essentiel | Spécifie le generic runner wrapper, base de tous les runners. ADR backing. |
| `PRD-MOC-KIX-MULTI-LANG-ECOSYSTEM-2026-09-24.md` | ✅ Utile | Formalise l'extension Rust/Go/Node et la gestion des processus système. Couverture multi-langage. |
| `PRD-MOC-KIX-EXE-ORCHESTRATION-2026-09-24.md` | ✅ Utile | Couvre toolchains, preflight, zombie monitor, doctor WAL. Réduit les faux positifs d'orchestration. |
| `PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-2026-09-24.md` | ⚠️ Remplacé | `superseded` par `PRD-MOC-KIX-MULTI-LANG-ECOSYSTEM-2026-09-24.md`. À archiver, pas de valeur ajoutée active. |
| `PRD-MOC-KIX-BOOTSTRAP-RUNNER-2026-08-20.md` | ✅ Essentiel | Formalise le runner d'amorçage, séparé de gateway-manager. Endpoints `/bootstrap/*`, ECOS CLI, watchdog. ADR backing. |
| `PRD-MOC-KIX-VEX-KIX-BOUNDARIES-20260927.md` | ✅ Essentiel | Contrat de frontières KIX/VEX. Points d'intégration autorisés, interdits, WAZAA bus, bootstrap coordination. |
| `PRD-MOC-KIX-BATMCP-20260928.md` | ✅ Utile | Formalise l'intégration BatMCP comme runner gateway-exe. Health checks, capability model, preuves d'exécution. |
| `PRD-MOC-KIX-ECOS-CLI-20260928.md` | ✅ Utile | Formalise l'intégration ECOS-CLI comme runner gateway-exe. BDCP, PAT rotation, bootstrap coordination. |

**Recommandation** : conserver les PRD MOC `MASTER`, `ORCHESTRATOR`, `MULTI-LANG`, `EXE-ORCHESTRATION`, `BOOTSTRAP-RUNNER`, `VEX-KIX-BOUNDARIES`, `BATMCP`, `ECOS-CLI`. Supprimer ou archiver `ECOSYSTEM-INTEGRATION` (remplacé).

### Mise à jour 2026-09-27 — Modèle de Rôle/Fonction

| Document | Mise à jour | Description |
|----------|-------------|-------------|
| `unified-design/designs/kix/design.yaml` | ✅ Ajout sections `roles`, `functional_roles`, `capability_model`, `dual_role_pattern`, `actor_model`, `adr_refs` | Modèle de rôle/fonction complet, 60 runners couverts, 21 catégories fonctionnelles |
| `unified-design/designs/kix-error-recovery/design.yaml` | ✅ Description enrichie | Référence au modèle de rôle/fonction KIX pour remediation triggers |
| `config/runners.yaml` | ✅ Ajout `meta.role` manquants | 5 runners complétés : friction-analyzer, agent-manager, nodex, rootx, kg-l-coherence-watchdog |
| `PRD-MOC-KIX-MASTER.md` | ✅ Section 2.3 + 2.3.6 + 2.3.7 | Documentation du modèle de rôle/fonction + constats dryrun causal + implémentation capability model |
| `PRD-MOC-KIX-ORCHESTRATOR-2026-08-18.md` | ✅ Section 4.4 | Documentation du modèle de rôle/fonction |
| `PRD-MOC-KIX-MULTI-LANG-ECOSYSTEM-2026-09-24.md` | ✅ Section 9 | Documentation du modèle de rôle/fonction pour runners Rust/Go/Node |
| `PRD-MOC-KIX-EXE-ORCHESTRATION-2026-09-24.md` | ✅ Section 11 | Documentation du modèle de rôle/fonction pour exe/orchestration |
| `PRD-MOC-VEX-KIX-BOUNDARIES-20260927.md` | ✅ Section 14 | Documentation du modèle de rôle/fonction pour les frontières KIX/VEX |
| `src/capability.py` | ✅ Nouveau fichier | Capability registry (7 capabilities) |
| `src/auth.py` | ✅ `requires_capability` decorator | Vérification capability dans les endpoints |
| `src/app.py` | ✅ 11 endpoints mis à jour | `@requires_capability` sur start/stop/restart/doctor/audit/schedules/release-handles |
| `tests/test_capability.py` | ✅ Nouveau fichier | 6 tests passants pour capability model |

**IntentHash** : 0xPRD_MOC_KIX_MASTER_20260902  
**Status** : completed  
**Date** : 2026-09-02  
**Dernière mise à jour** : 2026-09-27
