---
type: "PRD_MOC"
citizen: "L2-PLATFORM"
layer: "L2"
author: gerivdb
source_repo: gerivdb/KIX
source_path: PRD-MOC/PRD-MOC-KIX-BOOTSTRAP-RUNNER-2026-08-20.md
parent_doc: PRD-MOC-KIX-MASTER.md
related_adr: ADR-2026-08-20-001-bootstrap-runner.md, ADR-2026-08-18-002-KIX-GENERIC-RUNNER-WRAPPER.md, ADR-2026-07-27-016-kix-orchestrator
related_moc: PRD-MOC-KIX-MASTER.md, PRD-MOC-KIX-ORCHESTRATOR-2026-08-18.md, PRD-MOC-KIX-EXE-ORCHESTRATION-2026-09-24.md, PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER-2026-09-27.md
version: "1.0.0"
date: "2026-09-27"
status: "implemented"
intent_hash: "0xKIX_BOOTSTRAP_RUNNER_20260820"
mox_gates:
  - P-301
  - P-302
  - P-303
---

# PRD MOC - KIX - Bootstrap Runner — Orchestrateur d'Amorçage

## 1. RESUME EXECUTIF

Ce PRD MOC couvre le **runner `bootstrap` dédié** à KIX (port 8810) : orchestrateur d'amorçage de l'écosystème gerivdb, responsable de la séquence de démarrage ordonnée des services critiques, de l'enregistrement des services auprès de KIX, et de la publication de l'état de readiness global.

**Rôle KIX dans l'architecture** :
- **Séparation** : le bootstrap n'est plus couplé à `gateway-manager` (ADR-2026-08-20-001 accepté)
- **Runner dédié** : service Python intégré à KIX, `services/bootstrap_runner.py`
- **Responsabilité** : séquence de boot, `/bootstrap/ready`, `/bootstrap/status`, `/bootstrap/register`, `/bootstrap/monitor`
- **Intégration** : ECOS CLI, KIX API, WAZAA bus, VEX (L3)

**Source** : ADR-2026-08-20-001-bootstrap-runner.md + docs/bootstrap-runner.md
**IntentHash** : `0xKIX_BOOTSTRAP_RUNNER_20260820`
**Statut** : **implemented** (2026-09-27)

---

## 2. CONTEXTE ET PERIMETRE

### 2.1 Contexte

Historiquement, le runner `gateway-manager` (port 9000) était marqué `bootstrap: true` dans `config/runners.yaml`. Cela créait une ambiguïté de rôle :
- `gateway-manager` est un exécutable externe (BDCP proxy, PAT rotation).
- Le bootstrap nécessite des fonctionnalités spécifiques : `SecretResolver`, `KIXRegistrar`, endpoints `/bootstrap/*`, séquence de démarrage ordonnée.

**ADR-2026-08-20-001** a tranché : **Option B** — créer un runner `bootstrap` séparé, retirer `bootstrap: true` de `gateway-manager`.

### 2.2 Périmètre

| Composant | Rôle | État |
|-----------|------|------|
| **Bootstrap runner** | Service Python intégré à KIX, port 8810 | ✅ **IMPLÉMENTÉ** |
| **Endpoints `/bootstrap/*`** | `/health`, `/bootstrap/status`, `/bootstrap/ready`, `/bootstrap/start`, `/bootstrap/register`, `/bootstrap/monitor` | ✅ **IMPLÉMENTÉ** |
| **KIXRegistrar** | Enregistrement automatique des services dans KIX | ✅ **IMPLÉMENTÉ** |
| **SecretResolver** | Gestion dynamique des secrets via `$env:VAR` ou keyring | ✅ **IMPLÉMENTÉ** |
| **Self-Healing Watchdog** | Re-vérification périodique des dépendances, auto-restart | ✅ **IMPLÉMENTÉ** |
| **ECOS CLI integration** | Polling `/bootstrap/ready` avec budget 30s | ✅ **IMPLÉMENTÉ** |
| **WAZAA bus events** | Publication d'événements bootstrap | ✅ **IMPLÉMENTÉ** |

---

## 3. ARCHITECTURE

### 3.1 Principe Fondateur

**KIX sépare l'orchestrateur d'amorçage (`bootstrap`, port 8810) du proxy BDCP (`gateway-manager`, port 9000).**

```
┌─────────────────────────────────────────────────────────────┐
│                     ECOS CLI / BOOT                           │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                     KIX (port 8800)                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  RunnerBase │  │  Registry   │  │  Doctor     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│         │                │                │                 │
│         ▼                ▼                ▼                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              runners.yaml (déclaratif)               │   │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐       │   │
│  │  │ kix    │ │gateway │ │ trixd  │ │ wazaa  │ ...    │   │
│  │  └────────┘ └────────┘ └────────┘ └────────┘       │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                  bootstrap (port 8810)                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  • CHECK: gateway-manager (port 9000)               │   │
│  │  • CHECK: KIX self-check (port 8800)                │   │
│  │  • START: Arbiter (port 8742)                       │   │
│  │  • START: wazaa KG-L bus (port 1873)                │   │
│  │  • START/CHECK: trixd (port 7243)                   │   │
│  │  • CHECK: flex-api (port 8080, optional)            │   │
│  │  • REGISTER: register all services in KIX           │   │
│  │  • PUBLISH: /bootstrap/ready = true                 │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Matrice de Responsabilités

| Domaine | bootstrap (8810) | gateway-manager (9000) |
|---------|-----------------|------------------------|
| **Bootstrap sequence** | ✅ Responsable | ❌ Hors périmètre |
| **SecretResolver** | ✅ Responsable | ❌ Hors périmètre |
| **KIXRegistrar** | ✅ Responsable | ❌ Hors périmètre |
| **BDCP proxy / Clapet** | ❌ Hors périmètre | ✅ Responsable |
| **PAT rotation** | ❌ Hors périmètre | ✅ Responsable |
| **Endpoints `/bootstrap/*`** | ✅ Responsable | ❌ Hors périmètre |
| **Health check** | ✅ `/health` (8810) | ✅ `/health` (9000) |

### 3.3 Lifecycle States

```
                     +----------+
                     | PENDING  | <- KIX starts, waits for bootstrap
                     +----+-----+
                          |
                     +----+-----+
                     | CHECKING | <- Checking prerequisites
                     +----+-----+
                          |
            +-------------+-------------+
            |             |             |
            v             v             v
      +----------+   +----------+   +----------+
      | STARTING |   |  READY   |   | FAILED   |
      | (start   |   | (all     |   | (critical|
      | services)|   | services |   |  blocker)|
      +----------+   | running) |   +----------+
                     +----------+
```

### 3.4 Startup Sequence

```
ECOS CLI
  -> BDCP-CORE (gateway-manager, port 9000)
  -> KIX (port 8800) starts in "bootstrap pending" mode
  -> bootstrap (port 8810) starts automatically
      -> CHECK: gateway-manager (port 9000)
      -> CHECK: KIX self-check (port 8800)
      -> START: Arbiter (port 8742) via start-git-arbiter.ps1 (CMD wrapper + port wait)
      -> START: wazaa KG-L bus (port 1873) via src/bus_runner.py
      -> START/CHECK: trixd (port 7243) via KIX internal channel (X-KIX-Bootstrap)
      -> CHECK: wazaa-mc mission control (port 5002, optional)
      -> CHECK: flex-api (port 8080, optional)
      -> REGISTER: register all services in KIX
      -> PUBLISH: /bootstrap/ready = true when all required deps are up
   -> ECOS CLI polls /bootstrap/ready (Invoke-BootstrapGate, budget 30s,
      escape hatch ECOS_SKIP_BOOTSTRAP=1)
   -> Ecosystem operational
```

---

## 4. ENDPOINTS API

| Endpoint | Méthode | Description | Response |
|----------|---------|-------------|----------|
| `/health` | GET | Basic health check | `200 OK` |
| `/bootstrap/status` | GET | Detailed status of all services | `200 OK` + JSON |
| `/bootstrap/ready` | GET | Check if system is ready | `200 OK` or `503 Service Unavailable` |
| `/bootstrap/start` | POST | Trigger manual startup | `202 Accepted` |
| `/bootstrap/register` | POST | Register a service in KIX (`{"name","port","status?"}`) | `200 OK` / `400` / `502` |
| `/bootstrap/monitor` | GET | One-shot monitoring report with alert status | `200 OK` or `503` |

### 4.1 Endpoint `/bootstrap/register`

**Contrat** :
- Accepte un payload JSON `{"name", "port", "status?"}`
- Enregistre le service dans KIX via `KIXRegistrar`
- Retourne `200 OK` si succès, `400` si payload invalide, `502` si KIX injoignable

### 4.2 Endpoint `/bootstrap/ready`

**Contrat** :
- Retourne `{"ready": true}` quand tous les services requis sont opérationnels
- Retourne `503 Service Unavailable` + JSON avec `blockers` si des dépendances sont manquantes
- ECOS CLI poll avec budget 30s (`Invoke-BootstrapGate`)

---

## 5. SECURITY

### 5.1 BDCP Inviolable

Le bootstrap runner ne appelle **jamais** `POST /clapet/open`. Il respecte le mode BDCP permanent.

### 5.2 SecretResolver

- **Jamais** de secrets en clair dans `runners.yaml`
- Résolution via `$env:VAR` ou `keyring.get_password("gerivdb", var_name)`
- Filtrage systématique avant publication (regex secrets/PII)

### 5.3 Authentification

Les endpoints sensibles (`/bootstrap/start`) peuvent être protégés par JWT (rôles `admin`, `operator`).

---

## 6. SELF-HEALING WATCHDOG

Un daemon thread re-vérifie toutes les dépendances tous les `BOOTSTRAP_CHECK_INTERVAL` seconds (défaut : **3**) et re-exécute la séquence de démarrage quand une dépendance requise est down et qu'aucune séquence n'est déjà en cours.

**Recovery mesurée** : kill WAZAA bus → port back up en **8.1 s**, sous la cible PRD §11 de 10 s.

**Procédure de décommissionnement** : arrêter le bootstrap runner lui-même d'abord.

---

## 7. CONFIGURATION DECLARATIVE

Dans `config/runners.yaml` :

```yaml
- name: bootstrap
  runner_type: python
  port: 8810
  working_dir: D:/DO/WEB/TOOLS/L2-PLATFORM/KIX
  entrypoint: services/bootstrap_runner.py
  bootstrap: true
  auto_start: true
  health_path: /health
  restart_policy: on-failure
  log_file: D:/DO/WEB/TOOLS/L2-PLATFORM/KIX/logs/bootstrap.log
  dependencies:
    - gateway-manager
    - kix
    - arbiter
    - trixd
    - wazaa
    - flex-api
  kgl_schema: schemas/runners/bootstrap-status.schema.json
  meta:
    repo: gerivdb/GOVERNANCE-HUB
    role: bootstrap orchestrator
    intent_hash: 0xINTENT_BOOTSTRAP_RUNNER_GOVERNANCE_20260820
```

---

## 8. INTEGRATION ECOS CLI

ECOS CLI (`C:\DevTools\bin\ecos.ps1`) poll `/bootstrap/ready` après avoir démarré KIX :

```powershell
$bootstrapUrl = "http://127.0.0.1:8810/bootstrap/ready"
$bootstrapReady = $false
for ($i = 1; $i -le 30; $i++) {
    try {
        $resp = Invoke-RestMethod -Uri $bootstrapUrl -Method Get -TimeoutSec 1 -ErrorAction SilentlyContinue
        if ($resp -and $resp.ready -eq $true) {
            Write-Host "[BOOTSTRAP] Ready: all services operational" -ForegroundColor Green
            $bootstrapReady = $true
            break
        }
    } catch {
        # bootstrap not ready yet
    }
    Write-Host "[BOOTSTRAP] Waiting for bootstrap... ($i/30)" -ForegroundColor Yellow
    Start-Sleep -Seconds 1
}
if (-not $bootstrapReady) {
    Write-Host "[BOOTSTRAP] DEGRADED: bootstrap did not become ready in time" -ForegroundColor Red
}
```

---

## 9. MONITORING

### 9.1 Endpoint `/bootstrap/monitor`

| Endpoint | Méthode | Description | Response |
|----------|---------|-------------|----------|
| `/bootstrap/monitor` | GET | Monitoring d'alerte | `200 OK` ou `503` + JSON |

### 9.2 Alertes générées

- `bootstrap failed` : phase FAILED
- `bootstrap blockers: ...` : blockers présents
- `bootstrap not ready` : pas prêt hors phase PENDING

### 9.3 Intégration KIX

L'endpoint `/bootstrap/monitor` peut être interrogé par KIX pour détecter les défaillances bootstrap et déclencher des alertes via le système de notifications existant.

---

## 10. DEPENDANCES

### 10.1 Internes KIX

| Fichier | Rôle |
|---------|------|
| `services/bootstrap_runner.py` | Service bootstrap principal |
| `config/runners.yaml` | Registry déclaratif (runner `bootstrap`) |
| `src/app.py` | API REST KIX (endpoints `/bootstrap/*`) |
| `src/runner_state.py` | Store état runners KIX |
| `libs/shared-clients/win32_process.py` | Primitives déploiement Windows |

### 10.2 Externes

| Service | Port | Rôle |
|---------|------|------|
| `gateway-manager` | 9000 | BDCP proxy, vérifié par bootstrap |
| `KIX API` | 8800 | Self-check, enregistrement services |
| `Arbiter` | 8742 | Git arbiter, démarré par bootstrap |
| `WAZAA` | 1873 | KG-L bus, démarré par bootstrap |
| `trixd` | 7243 | Runtime Zig, démarré/checké par bootstrap |
| `flex-api` | 8080 | Cache/Flex, checké par bootstrap (optional) |

---

## 11. TRACABILITE

### 11.1 Thought Chain

```yaml
thought_chain:
  - source: "Observation : gateway-manager cumule BDCP proxy et bootstrap, responsabilités mélangées"
    artifact: "Risque d'ambiguïté, impossible d'ajouter SecretResolver/KIXRegistrar à un exe externe"
    intent_hash: "0xKIX_BOOTSTRAP_RUNNER_20260820"
  - source: "Déduction : nécessité d'un runner bootstrap dédié, Python, intégré à KIX"
    artifact: "ADR-2026-08-20-001 acceptée : Option B"
    intent_hash: "0xKIX_BOOTSTRAP_RUNNER_20260820"
  - source: "Validation : bootstrap runner implémenté, endpoints /bootstrap/* opérationnels, ECOS CLI intégré"
    artifact: "PRD-MOC-KIX-BOOTSTRAP-RUNNER-2026-08-20.md"
    intent_hash: "0xKIX_BOOTSTRAP_RUNNER_20260820"
```

### 11.2 Gates

| Gate | Critère | Statut |
|------|---------|--------|
| **P-301** | ADR-2026-08-20-001 acceptée | ✅ VALIDÉ |
| **P-302** | Endpoints `/bootstrap/*` implémentés et testés | ✅ VALIDÉ |
| **P-303** | ECOS CLI integration + watchdog self-healing | ✅ VALIDÉ |

### 11.3 Modèle de Rôle/Fonction KIX

Ce PRD MOC s'aligne sur le modèle de rôle/fonction défini dans `PRD-MOC-KIX-MASTER.md` section 2.3 :

- **RBAC** : `admin`, `operator`, `viewer` (JWT dans `src/auth.py`)
- **Functional Roles** : 21 catégories (`orchestrator`, `cognitive`, `governance`, `infrastructure`, etc.)
- **Capability Model** : 7 capabilities (`runner-lifecycle`, `process-manager`, `pid-tracker`, `exe-launcher`, etc.)
- **Dual-Role Pattern** : TRIX/TRIXD/PLIX = RLM + TLM
- **ActorSpec** : intégration via `KIXProcessManagerAdapter`

Le runner `bootstrap` utilise les capabilities suivantes :
- `runner:start` — démarrer les services dépendants
- `runner:stop` — arrêter les services en erreur
- `process:restart` — redémarrer les processus zombies
- `health:check` — vérifier la santé des dépendances

---

## 12. PREUVE-OF-LIFE

- [x] 2026-08-20T00:00:00+02:00 — ADR-2026-08-20-001 acceptée : Option B (runner bootstrap séparé)
- [x] 2026-08-20T00:00:00+02:00 — Runner `bootstrap` ajouté dans `config/runners.yaml`
- [x] 2026-08-20T00:00:00+02:00 — `bootstrap: true` retiré de `gateway-manager`
- [x] 2026-08-20T00:00:00+02:00 — `services/bootstrap_runner.py` créé et fonctionnel
- [x] 2026-08-20T00:00:00+02:00 — Endpoints `/bootstrap/*` opérationnels (health, status, ready, start, register, monitor)
- [x] 2026-08-20T00:00:00+02:00 — ECOS CLI intégré (`Invoke-BootstrapGate`, budget 30s)
- [x] 2026-08-20T00:00:00+02:00 — Self-healing watchdog actif (interval 3s, recovery 8.1s)
- [x] 2026-09-27T06:49:00+02:00 — PRD-MOC-KIX-BOOTSTRAP-RUNNER créé et référencé dans PRD-MOC-KIX-MASTER.md
- [x] 2026-09-27T23:00:00+02:00 — Modèle de rôle/fonction documenté dans PRD-MOC-KIX-MASTER.md section 2.3.7
- [x] 2026-09-27T23:00:00+02:00 — Capability model implémenté : `src/capability.py` + `requires_capability` decorator
- [x] 2026-09-28T01:16:14+02:00 — 24 endpoints KIX protégés par `@requires_capability` (start/stop/restart/doctor/audit/schedules/release-handles/health/logs/metrics/swarm/alerts/events/notifications/dashboard)
- [x] 2026-09-28T01:16:14+02:00 — Tests d'intégration corrigés : 13 passants (auth capability appliqué)

---

## 13. REFERENCES

- `docs/bootstrap-runner.md` : Documentation technique bootstrap runner
- `docs/runbook-bootstrap.md` : Runbook relance manuelle bootstrap
- `ADR-2026-08-20-001-bootstrap-runner.md` : ADR séparation bootstrap/gateway-manager
- `PRD-MOC-KIX-MASTER.md` : Master MOC KIX
- `PRD-MOC-KIX-ORCHESTRATOR-2026-08-18.md` : PRD MOC orchestrateur generic runner wrapper
- `PRD-MOC-KIX-EXE-ORCHESTRATION-2026-09-24.md` : Orchestration exécutables / preflight / zombie monitor
- `config/runners.yaml` : Registry déclaratif KIX
- `services/bootstrap_runner.py` : Implémentation bootstrap runner

---

**IntentHash** : `0xKIX_BOOTSTRAP_RUNNER_20260820`
**Status** : implemented
**Date** : 2026-09-27

*PRD-MOC-KIX-BOOTSTRAP-RUNNER — implemented — 2026-09-27*
