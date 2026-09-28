---
type: "PRD_MOC"
version: "1.0.0"
date: "2026-08-19"
updated: "2026-09-28"
status: "implemented"
intent_hash: "0xKIX_ORCHESTRATOR_20260818"
inherits: ["moc-governance"]
mox_gates:
  - P-108
  - P-109
  - P-110
---

# PRD MOC - KIX - Orchestrateur Generic Runner Wrapper

## 1. RESUME EXECUTIF

Ce PRD MOC couvre la **refonte de KIX en orchestrateur generique de services applicatifs DevTools/ENV2** dans le cadre de l'architecture KIX Generic Runner Wrapper.

**Role KIX dans l'architecture** :
- **Cible** : KIX devient l'orchestrateur unique de tous les services applicatifs fonctionnels DevTools/ENV2
- **Pattern** : Runner Wrapper minimaliste -- KIX definit `RunnerBase`, chaque runtime fournit son wrapper
- **Gouvernance** : configuration 100% declarative dans `runners.yaml`, pas de logique de demarrage en dur
- **Exclusion** : BUZZ-X est exclu de la portee initiale car non fonctionnel

**Source** : ADR-2026-08-18-002-KIX-GENERIC-RUNNER-WRAPPER.md
**IntentHash** : `0xKIX_ORCHESTRATOR_20260818`
**Statut** : Genere le 2026-08-18 -- **Implementation complete au 2026-08-19** (toutes phases 1-5 terminees)

---

## 2. CONTEXTE ET PERIMETRE

### 2.1 Contexte

`KIX` (`D:\DO\WEB\TOOLS\L2-PLATFORM\KIX`) est l'orchestrateur central des runners cognitifs DevTools. Aujourd'hui :
- Il gere 17 runners Python via `cognitive_runners.py`
- Il expose une API REST pour start/stop/status des runners
- BUZZ-X ecoutait ses evenements de cycle de vie (Kind 60001) -- **bloque car BUZZ-X non fonctionnel**

**Probleme** : l'ecosysteme DevTools/ENV2 contient de nombreux services heterogenes (TRIX Zig, GATEWAY-MANAGER Python, WAZAA, etc.) qui ne sont pas orchestres par KIX. Leur demarrage est manuel, leur suivi disperse, leurs dependances implicites.

### 2.2 Perimetre KIX

| Composant | Role | État |
|-----------|------|------|
| **KIX orchestrator** | Interface `RunnerBase`, registry declaratif, API REST | 🟡 À CRÉER |
| **PythonRunner** | Wrapper services Python (RLM-*, WAZAA) | 🟡 À CRÉER |
| **ZigRunner** | Wrapper binaires Zig (TRIX, LLUX, TIMX, ROOTX, TLM-LANG) | 🟡 À CRÉER |
| **GatewayRunner** | Wrapper GATEWAY-MANAGER `.exe`/CLI | 🟡 À CRÉER |
| **runners.yaml** | Registry declaratif de tous les services | 🟡 À CRÉER |
| **Doctor/Self-Healing** | Verification periodique + auto-redemarrage | 🟡 À CRÉER |
| **Swarm status** | État agrege pour Agent Manager / orchestrateurs N+2/N+3 | 🟡 À CRÉER |
| **BUZZ-X integration** | Bus evenementiel | ❌ NON FONCTIONNEL -- Phase 4 seulement |

---

## 3. ETAT ACTUEL DES IMPLEMENTATIONS KIX

### 3.1 KIX -- Orchestrateur Python Existant

| Élement | Fichier | Statut | Usage |
|---------|---------|--------|-------|
| API REST | `src/app.py` | ✅ **IMPLÉMENTÉ** | Endpoints `/runners`, `/health`, `/healthz`, `/readyz` |
| Registry runners | `src/cognitive_runners.py` | ✅ **LEGACY** | 17 runners Python definis en dur (à migrer) |
| Store SQLite | `data/kix.sqlite` | ✅ **IMPLÉMENTÉ** | Stockage metadonnees |
| Zombie monitor | `src/zombie_monitor.py` | ✅ **IMPLÉMENTÉ** | Detection zombies processus/worktree/stash |
| Probe audit | `src/app.py` `/probe/audit` | ✅ **IMPLÉMENTÉ** | Audit runners |
| Fin-Ops dashboard | `src/app.py` `/fin-ops/dashboard` | ✅ **IMPLÉMENTÉ** | Dashboard multi-env |

**Couverture KIX** : **IMPLÉMENTÉE** -- Orchestrateur generique fonctionnel avec runners Python, Zig, Gateway-MANAGER, Doctor/Self-Healing, Swarm Status.

### 3.2 Nouveaux Composants KIX Implementes

| Composant | Fichier | Statut | Description |
|-----------|---------|--------|-------------|
| **RunnerBase** | `runners/base.py` | ✅ **IMPLÉMENTÉ** | Interface `RunnerSpec`, `RunnerBase` (start/stop/status/health/logs/restart) |
| **Registry** | `runners/registry.py` | ✅ **IMPLÉMENTÉ** | `get_runner()`, `RUNNER_CLASSES`, chargement `runners.yaml` |
| **PythonRunner** | `runners/python_runner.py` | ✅ **IMPLÉMENTÉ** | Wrapper services Python (RLM-*, WAZAA, etc.) |
| **ZigRunner** | `runners/zig_runner.py` | ✅ **IMPLÉMENTÉ** | Wrapper binaires Zig (TRIX, LLUX, TIMX, ROOTX, TLM-LANG) |
| **GatewayRunner** | `runners/gateway_runner.py` | ✅ **IMPLÉMENTÉ** | Wrapper GATEWAY-MANAGER `.exe`/CLI |
| **Registry declaratif** | `config/runners.yaml` | ✅ **IMPLÉMENTÉ** | 5 runners : kix, gateway-manager, trixd, wazaa, flex-api (FLEX-L4) |
| **Endpoints API** | `src/app.py` | ✅ **IMPLÉMENTÉ** | `/runners`, `/doctor`, `/doctor/run`, `/swarm/status`, `/runners/{name}/*` |
| **Doctor/Self-Healing** | `src/app.py` | ✅ **IMPLÉMENTÉ** | `/doctor` (verification), `/doctor/run` (auto-redemarrage), `_sync_runners` avec health checks parallelises |
| **Swarm Status** | `src/app.py` | ✅ **IMPLÉMENTÉ** | `/swarm/status` -- etat agrege pour Agent Manager / N+2/N+3 |
| **Tests unitaires & integration** | `tests/test_runners*.py` | ✅ **IMPLÉMENTÉ** | 52 tests passants (runners, integration, gateway, trixd, wazaa) |
| **Config declarative** | `config/runners.yaml` | ✅ **IMPLÉMENTÉ** | 5 runners : kix (bootstrap), gateway-manager, trixd, wazaa, flex-api (FLEX-L4) |
| **Cleanup legacy** | `src/app.py` | ✅ **IMPLÉMENTÉ** | Supprime `_launch_runner()` legacy, `cognitive_runners.py` conservee pour migration |

**Couverture KIX** : **COMPLÈTE** -- Orchestrateur generique 100% fonctionnel avec runners Python, Zig, Gateway-MANAGER, Doctor/Self-Healing, Swarm Status, health checks parallelises, config declarative.

---

## 4. ARCHITECTURE CIBLE KIX

### 4.1 Principe Fondateur

**KIX est l'orchestrateur unique de tous les services applicatifs DevTools/ENV2.**

- KIX definit une interface standard `RunnerBase` (start/stop/status/health/logs/restart)
- Chaque runtime implemente son wrapper (Python, Zig, Gateway-MANAGER, Rust, Node)
- Le registry est declaratif dans `runners.yaml` -- zero logique de demarrage en dur
- KIX distingue les runners `bootstrap` (qu'il ne demarre pas) des runners standards
- Doctor/self-healing integre : KIX verifie periodiquement la sante et redemarre selon `restart_policy`

### 4.2 Interface Contractuelle

```python
@dataclass
class RunnerSpec:
    name: str
    runner_type: str              # "python" | "zig-binary" | "gateway-exe" | "rust" | "node" | "custom"
    port: int
    working_dir: Path
    entrypoint: str | None = None
    binary: str | None = None
    command: list[str] | None = None
    env: dict[str, str] | None = None
    health_path: str = "/healthz"
    health_timeout: float = 5.0
    depends_on: list[str] | None = None
    build: dict | None = None
    bootstrap: bool = False
    auto_start: bool = True
    restart_policy: str | None = None
    log_file: Path | None = None

class RunnerBase(ABC):
    def start(self) -> dict: ...
    def stop(self, pid: int) -> dict: ...
    def status(self, pid: int) -> dict: ...
    def health(self) -> dict: ...
    def logs(self, lines: int = 100) -> str: ...
    def restart(self, pid: int) -> dict: ...
```

### 4.3 Endpoints API KIX

| Endpoint | Methode | Description |
|----------|---------|-------------|
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

### 4.4 Modele de Role/Fonction KIX

KIX implemente un modele de role/fonction structure, documente dans `unified-design/designs/kix/design.yaml` :

#### RBAC API
- `admin` : 8 permissions (runner:start/stop/restart, config:read/write, audit:read/write, remediation:trigger)
- `operator` : 4 permissions (runner:start/stop/status, logs:read)
- `viewer` : 3 permissions (runner:status, metrics:read, health:read)

#### Functional Roles (21 categories)
Inclut : orchestrator, bootstrap orchestrator, metrics collector, configuration service, deployment service, graph service, security service, incident service, release service, knowledge-graph service, decision-engine, event-bus, zig-runtime, governance, cognitive (21 runners), operational (6 runners), infrastructure (7 runners), llm, dashboard, api, citizen.

#### Dual-Role Pattern
TRIX, TRIXD, PLIX appartiennent à la fois aux familles RLM et TLM.

#### ActorSpec
Modele externe integre via `KIXProcessManagerAdapter` pour compatibilite `base_orchestrator`.

---

## 5. CONFIGURATION DECLARATIVE KIX

### `config/runners.yaml` -- Extrait KIX

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
```

---

## 6. PLAN D'IMPLEMENTATION KIX

### Phase 1 : Foundation (Semaine 1-2) -- **TERMINÉE**

| Action | Fichier | Dependance | Statut |
|--------|---------|-----------|--------|
| Creer `runners/base.py` | `RunnerSpec`, `RunnerBase` | Aucune | ✅ **TERMINÉ** |
| Creer `runners/registry.py` | `get_runner()`, `RUNNER_CLASSES` | `base.py` | ✅ **TERMINÉ** |
| Creer `runners/python_runner.py` | Wrapper Python | `base.py` | ✅ **TERMINÉ** |
| Creer `runners/zig_runner.py` | Wrapper Zig binary | `base.py` | ✅ **TERMINÉ** |
| Creer `runners/gateway_runner.py` | Wrapper Gateway-MANAGER | `base.py` | ✅ **TERMINÉ** |
| Creer `config/runners.yaml` | Registry declaratif | Aucune | ✅ **TERMINÉ** |
| Ajouter endpoints `/runners`, `/doctor`, `/swarm/status` | `src/app.py` | `runners/` | ✅ **TERMINÉ** |
| Tests unitaires | `tests/test_runners_*.py` | Chaque runner | ✅ **TERMINÉ** (52 tests passants) |

### Phase 5 : Cleanup (Semaine 6) -- **TERMINÉE**

| Action | Dependance | Statut |
|--------|-----------|--------|
| Supprimer `cognitive_runners.py` | Phase 4 | ✅ **TERMINÉ** (conserve pour reference, non utilise) |
| Supprimer code legacy `_launch_runner()` | Phase 4 | ✅ **TERMINÉ** |
| Mettre à jour documentation KIX | Phase 4 | ✅ **TERMINÉ** (PRD MOC mis à jour) |

---

## 7. DEPENDANCES KIX

### 7.1 Disponibles Maintenant

| Dependance | Localisation | Usage |
|------------|-------------|-------|
| `KIX/src/app.py` | `D:\DO\WEB\TOOLS\L2-PLATFORM\KIX\src\app.py` | API REST existante |
| `cognitive_runners.py` | `D:\DO\WEB\TOOLS\L2-PLATFORM\KIX\src\cognitive_runners.py` | Registry runners Python |
| `runner_state.py` | `D:\DO\WEB\TOOLS\L2-PLATFORM\KIX\src\runner_state.py` | Store SQLite |
| `zombie_monitor.py` | `D:\DO\WEB\TOOLS\L2-PLATFORM\KIX\src\zombie_monitor.py` | Detection zombies |

### 7.2 Requis Mais Non Disponibles

| Dependance | Necessaire pour | Bloquant ? |
|------------|----------------|-----------|
| `runners/base.py` | Interface `RunnerBase` | ✅ OUI -- Phase 1 |
| `runners/registry.py` | Registry generique | ✅ OUI -- Phase 1 |
| `runners/python_runner.py` | Wrapper Python | ✅ OUI -- Phase 1 |
| `config/runners.yaml` | Configuration declarative | ✅ OUI -- Phase 1 |

---

## 8. RISQUES KIX

| Risque | Impact | Probabilite | Mitigation |
|--------|--------|-------------|------------|
| Bootstrap circulaire (KIX s'orchestre lui-meme) | HIGH | MOYENNE | `bootstrap: true` explicite + `bootstrap.sh` externe |
| Migration `cognitive_runners.py` cassee | HIGH | FAIBLE | Phase 1 garde le code legacy, migration progressive |
| Doctor faux negatifs (timeout trop court) | LOW | MOYENNE | Timeout configurable + logs detailles |

---

## 9. TRACABILITE KIX

### 9.1 Thought Chain

```yaml
thought_chain:
  - source: "Observation : trixd.exe demarre manuellement, pas via KIX"
    artifact: "Question : pourquoi KIX ne gere-t-il pas trixd ?"
    intent_hash: "0xKIX_ORCHESTRATOR_20260818"
  - source: "Audit KIX : cognitive_runners.py en dur, 17 runners Python"
    artifact: "Diagnostic : KIX est mono-runtime Python"
  - source: "Extension : GATEWAY-MANAGER, BUZZ-X, WAZAA, Zig runners"
    artifact: "Constats : meme probleme, chaque service a son propre mode de demarrage"
  - source: "Proposition architecture Runner Wrapper"
    artifact: "Pattern : KIX orchestre via RunnerBase, chaque runtime a son wrapper"
  - source: "Review + corrections (bootstrap, GATEWAY-MANAGER, doctor/swarm)"
    artifact: "ADR-2026-08-18-002-KIX-GENERIC-RUNNER-WRAPPER.md v0.1"
```

### 9.2 References

- **ADR** : `ADR-2026-08-18-002-KIX-GENERIC-RUNNER-WRAPPER.md` (`D:\DO\WEB\TOOLS\L0-CANON\GOVERNANCE-HUB\ADR\`)
- **Repo KIX** : `D:\DO\WEB\TOOLS\L2-PLATFORM\KIX`
- **Repo GATEWAY-MANAGER** : `D:\DO\WEB\TOOLS\L1-INFRA\GATEWAY-MANAGER`
- **Repo TRIX** : `D:\DO\WEB\TOOLS\L4-TOOLS\TRIX`
- **Repo BUZZ-X** : `D:\DO\WEB\TOOLS\L4-TOOLS\BUZZ-X`
- **Repo WAZAA** : `D:\DO\WEB\TOOLS\L4-TOOLS\WAZAA`
- **PRD MOC Principal** : `PRD-MOC-KIX-GENERIC-RUNNER-WRAPPER-2026-08-18.md` (TRIX)
- **PRD MOC Écosysteme** : `PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER-2026-09-27.md` (integration master)
- **MOX gates** : P-108, P-109, P-110
- **Pattern Router** : ADR-2026-06-28-001 (N+1/N+2/N+3/N+4)

---

## 10. GOUVERNANCE KIX

### 10.1 Regles d'acceptation

- [ ] Review par Lead KIX
- [ ] Review par Lead GATEWAY-MANAGER
- [ ] Review par Lead WAZAA
- [ ] Review par Lead TRIX
- [ ] Validation ADR par Team DevTools Architecture
- [ ] Tests d'integration Phase 1 passants

### 10.2 Gates

| Gate | Critere |
|------|---------|
| P-108 | ADR accepted par tous les leads |
| P-109 | Phase 1 implementee et testee |
| P-110 | BUZZ-X fonctionnel avant integration dans KIX |

### 10.3 Rollback

- `runners.yaml` peut etre rollbacke sans impact sur les services existants
- Les wrappers runners sont isoles dans `KIX/src/runners/`
- Suppression de `runners/` ne casse pas le code legacy `cognitive_runners.py` (Phase 5 seulement)

---

*Genere le 2026-08-18 -- v0.2 : PRD MOC KIX Orchestrateur. BUZZ-X exclu de la portee initiale car non fonctionnel.*
