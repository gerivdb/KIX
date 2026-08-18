---
type: "PRD_MOC"
version: "0.2.0"
date: "2026-08-18"
status: "PROPOSED"
intent_hash: "0xKIX_ORCHESTRATOR_20260818"
inherits: ["moc-governance"]
mox_gates:
  - P-108
  - P-109
  - P-110
---

# PRD MOC - KIX - Orchestrateur Generic Runner Wrapper

## 1. RESUME EXECUTIF

Ce PRD MOC couvre la **refonte de KIX en orchestrateur générique de services applicatifs DevTools/ENV2** dans le cadre de l'architecture KIX Generic Runner Wrapper.

**Rôle KIX dans l'architecture** :
- **Cible** : KIX devient l'orchestrateur unique de tous les services applicatifs fonctionnels DevTools/ENV2
- **Pattern** : Runner Wrapper minimaliste — KIX définit `RunnerBase`, chaque runtime fournit son wrapper
- **Gouvernance** : configuration 100% déclarative dans `runners.yaml`, pas de logique de démarrage en dur
- **Exclusion** : BUZZ-X est exclu de la portée initiale car non fonctionnel

**Source** : ADR-2026-08-18-002-KIX-GENERIC-RUNNER-WRAPPER.md
**IntentHash** : `0xKIX_ORCHESTRATOR_20260818`
**Statut** : Généré le 2026-08-18 — reflète l'état cible, pas l'état actuel

---

## 2. CONTEXTE ET PERIMETRE

### 2.1 Contexte

`KIX` (`D:\DO\WEB\TOOLS\L2-PLATFORM\KIX`) est l'orchestrateur central des runners cognitifs DevTools. Aujourd'hui :
- Il gère 17 runners Python via `cognitive_runners.py`
- Il expose une API REST pour start/stop/status des runners
- BUZZ-X écoutait ses événements de cycle de vie (Kind 60001) — **bloqué car BUZZ-X non fonctionnel**

**Problème** : l'écosystème DevTools/ENV2 contient de nombreux services hétérogènes (TRIX Zig, GATEWAY-MANAGER Python, WAZAA, etc.) qui ne sont pas orchestrés par KIX. Leur démarrage est manuel, leur suivi dispersé, leurs dépendances implicites.

### 2.2 Périmètre KIX

| Composant | Rôle | État |
|-----------|------|------|
| **KIX orchestrator** | Interface `RunnerBase`, registry déclaratif, API REST | 🟡 À CRÉER |
| **PythonRunner** | Wrapper services Python (RLM-*, WAZAA) | 🟡 À CRÉER |
| **ZigRunner** | Wrapper binaires Zig (TRIX, LLUX, TIMX, ROOTX, TLM-LANG) | 🟡 À CRÉER |
| **GatewayRunner** | Wrapper GATEWAY-MANAGER `.exe`/CLI | 🟡 À CRÉER |
| **runners.yaml** | Registry déclaratif de tous les services | 🟡 À CRÉER |
| **Doctor/Self-Healing** | Vérification périodique + auto-redémarrage | 🟡 À CRÉER |
| **Swarm status** | État agrégé pour Agent Manager / orchestrateurs N+2/N+3 | 🟡 À CRÉER |
| **BUZZ-X integration** | Bus événementiel | ❌ NON FONCTIONNEL — Phase 4 seulement |

---

## 3. ETAT ACTUEL DES IMPLEMENTATIONS KIX

### 3.1 KIX — Orchestrateur Python Existant

| Élément | Fichier | Statut | Usage |
|---------|---------|--------|-------|
| API REST | `src/app.py` | ✅ | Endpoints `/runners`, `/health`, `/healthz`, `/readyz` |
| Registry runners | `src/cognitive_runners.py` | ✅ | 17 runners Python définis en dur |
| Store SQLite | `data/kix.sqlite` | ✅ | Stockage métadonnées |
| Zombie monitor | `src/zombie_monitor.py` | ✅ | Détection zombies processus/worktree/stash |
| Probe audit | `src/app.py` `/probe/audit` | ✅ | Audit runners |
| Fin-Ops dashboard | `src/app.py` `/fin-ops/dashboard` | ✅ | Dashboard multi-env |

**Couverture KIX** : fonctionnel mais limité aux runners Python. Pas de support Zig/binary, pas de doctor/self-healing, pas de swarm status.

---

## 4. ARCHITECTURE CIBLE KIX

### 4.1 Principe Fondateur

**KIX est l'orchestrateur unique de tous les services applicatifs DevTools/ENV2.**

- KIX définit une interface standard `RunnerBase` (start/stop/status/health/logs/restart)
- Chaque runtime implémente son wrapper (Python, Zig, Gateway-MANAGER, Rust, Node)
- Le registry est déclaratif dans `runners.yaml` — zéro logique de démarrage en dur
- KIX distingue les runners `bootstrap` (qu'il ne démarre pas) des runners standards
- Doctor/self-healing intégré : KIX vérifie périodiquement la santé et redémarre selon `restart_policy`

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

| Endpoint | Méthode | Description |
|----------|---------|-------------|
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

## 5. CONFIGURATION DECLARATIVE KIX

### `config/runners.yaml` — Extrait KIX

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

### Phase 1 : Foundation (Semaine 1-2)

| Action | Fichier | Dépendance |
|--------|---------|-----------|
| Créer `runners/base.py` | `RunnerSpec`, `RunnerBase` | Aucune |
| Créer `runners/registry.py` | `get_runner()`, `RUNNER_CLASSES` | `base.py` |
| Créer `runners/python_runner.py` | Wrapper Python | `base.py` |
| Créer `runners/zig_runner.py` | Wrapper Zig binary | `base.py` |
| Créer `runners/gateway_runner.py` | Wrapper Gateway-MANAGER | `base.py` |
| Créer `config/runners.yaml` | Registry déclaratif | Aucune |
| Ajouter endpoints `/runners`, `/doctor`, `/swarm/status` | `src/app.py` | `runners/` |
| Tests unitaires | `tests/test_runners_*.py` | Chaque runner |

### Phase 5 : Cleanup (Semaine 6)

| Action | Dépendance |
|--------|-----------|
| Supprimer `cognitive_runners.py` | Phase 4 |
| Supprimer code legacy `_launch_runner()` | Phase 4 |
| Mettre à jour documentation KIX | Phase 4 |

---

## 7. DEPENDANCES KIX

### 7.1 Disponibles Maintenant

| Dépendance | Localisation | Usage |
|------------|-------------|-------|
| `KIX/src/app.py` | `D:\DO\WEB\TOOLS\L2-PLATFORM\KIX\src\app.py` | API REST existante |
| `cognitive_runners.py` | `D:\DO\WEB\TOOLS\L2-PLATFORM\KIX\src\cognitive_runners.py` | Registry runners Python |
| `runner_state.py` | `D:\DO\WEB\TOOLS\L2-PLATFORM\KIX\src\runner_state.py` | Store SQLite |
| `zombie_monitor.py` | `D:\DO\WEB\TOOLS\L2-PLATFORM\KIX\src\zombie_monitor.py` | Détection zombies |

### 7.2 Requis Mais Non Disponibles

| Dépendance | Nécessaire pour | Bloquant ? |
|------------|----------------|-----------|
| `runners/base.py` | Interface `RunnerBase` | ✅ OUI — Phase 1 |
| `runners/registry.py` | Registry générique | ✅ OUI — Phase 1 |
| `runners/python_runner.py` | Wrapper Python | ✅ OUI — Phase 1 |
| `config/runners.yaml` | Configuration déclarative | ✅ OUI — Phase 1 |

---

## 8. RISQUES KIX

| Risque | Impact | Probabilité | Mitigation |
|--------|--------|-------------|------------|
| Bootstrap circulaire (KIX s'orchestre lui-même) | HIGH | MOYENNE | `bootstrap: true` explicite + `bootstrap.sh` externe |
| Migration `cognitive_runners.py` cassée | HIGH | FAIBLE | Phase 1 garde le code legacy, migration progressive |
| Doctor faux négatifs (timeout trop court) | LOW | MOYENNE | Timeout configurable + logs détaillés |

---

## 9. TRACABILITE KIX

### 9.1 Thought Chain

```yaml
thought_chain:
  - source: "Observation : trixd.exe démarré manuellement, pas via KIX"
    artifact: "Question : pourquoi KIX ne gère-t-il pas trixd ?"
    intent_hash: "0xKIX_ORCHESTRATOR_20260818"
  - source: "Audit KIX : cognitive_runners.py en dur, 17 runners Python"
    artifact: "Diagnostic : KIX est mono-runtime Python"
  - source: "Extension : GATEWAY-MANAGER, BUZZ-X, WAZAA, Zig runners"
    artifact: "Constats : même problème, chaque service a son propre mode de démarrage"
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
- **MOX gates** : P-108, P-109, P-110
- **Pattern Router** : ADR-2026-06-28-001 (N+1/N+2/N+3/N+4)

---

## 10. GOUVERNANCE KIX

### 10.1 Règles d'acceptation

- [ ] Review par Lead KIX
- [ ] Review par Lead GATEWAY-MANAGER
- [ ] Review par Lead WAZAA
- [ ] Review par Lead TRIX
- [ ] Validation ADR par Team DevTools Architecture
- [ ] Tests d'intégration Phase 1 passants

### 10.2 Gates

| Gate | Critère |
|------|---------|
| P-108 | ADR accepted par tous les leads |
| P-109 | Phase 1 implémentée et testée |
| P-110 | BUZZ-X fonctionnel avant intégration dans KIX |

### 10.3 Rollback

- `runners.yaml` peut être rollbacké sans impact sur les services existants
- Les wrappers runners sont isolés dans `KIX/src/runners/`
- Suppression de `runners/` ne casse pas le code legacy `cognitive_runners.py` (Phase 5 seulement)

---

*Généré le 2026-08-18 — v0.2 : PRD MOC KIX Orchestrateur. BUZZ-X exclu de la portée initiale car non fonctionnel.*
