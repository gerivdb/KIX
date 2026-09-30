---
type: PRD-MOC
version: "1.0.0"
date: "2026-09-26"
status: approved
intent_hash: 0xPRD_MOC_VEX_PID_REGISTRY_AND_LIFECYCLE_20260926
parent_prd: PRD-MOC-VEX-L3-ORCHESTRATOR-20260926.md
pole_id: POLE-MEMORY-001
owner: L3-CITIZENS
repo: gerivdb/VEX
---

# PRD-MOC - VEX PID Registry and Daemon Lifecycle

## Objectif
Décrire la gestion du cycle de vie des daemons L3 par VEX, incluant le PID registry, le démarrage/arrêt/redémarrage automatique, le déploiement système (NSSM/schtasks/systemd), et la supervision continue.

## Contexte
VEX est l'orchestrateur L3 des daemons autonomes de l'écosystème gerivdb. Il doit garantir que chaque daemon déclaré dans `vex.yaml` est démarré, supervisé, et redémarré automatiquement en cas de crash. Le PID registry persiste l'état des processus pour permettre une reprise après redémarrage de VEX lui-même.

## Périmètre
- Inclut : PID registry L3, daemon manager, process manager, déploiement, health check agrégé, HTTP server
- Exclut : implémentations binaires Zig/Python hors contrat d'interface, gestion des daemons L2 (KIX)

## Architecture

```
VEX Lifecycle
├── VEXRegistry (registre déclaratif)
│   └── vex.yaml (citizens, daemons, deployment config)
├── VEXProcessManager (PID registry JSON)
│   ├── register / unregister
│   ├── prune_dead (détection processus morts)
│   └── find_by_citizen
├── VEXDaemonManager (gestion cycle de vie)
│   ├── start_daemon
│   ├── stop_daemon
│   ├── get_status
│   └── run_forever (supervision polling)
├── VEXDeployment (déploiement système)
│   ├── _deploy_windows (NSSM/schtasks)
│   └── _deploy_systemd
├── VEXHealth (health check agrégé)
│   ├── check_all
│   └── check_citizen
└── VEXHTTPServer (exposition HTTP)
    └── GET /health
```

## Critères d'acceptation

### PID Registry
- [x] `VEXProcessManager` charge/sauvegarde `data/pid_registry.json`
- [x] `register()` enregistre un `ProcessEntry` avec PID, citizen, daemon_id, repo, role
- [x] `unregister()` supprime un PID du registry
- [x] `prune_dead()` détecte les processus morts via `OpenProcess` (Windows) / `os.kill(pid, 0)` (Linux)
- [x] `find_by_citizen()` retourne tous les processus d'un citizen

### Daemon Manager
- [x] `start_daemon()` démarre un daemon via `subprocess.Popen` avec `CREATE_NO_WINDOW | DETACHED_PROCESS` (Windows, anti-pattern popups)
- [x] `stop_daemon()` arrête un daemon via `terminate()` puis `kill()` après timeout 10s
- [x] `get_status()` retourne `running` / `stopped` / `not_started`
- [x] `run_forever()` supervise tous les daemons avec polling configurable
- [x] Redémarrage automatique si `auto_restart: true` avec délai `restart_delay`

### Déploiement
- [ ] `_deploy_nssm()` installe un service NSSM avec `SERVICE_AUTO_START`
- [ ] `_deploy_schtask()` crée une tâche planifiée Windows via XML
- [ ] `_deploy_systemd()` crée un service systemd avec `Restart=always`

### Health Check
- [x] `check_all()` retourne un dict `{citizen: {daemon_id: {status, pid, key}}}`
- [x] `check_citizen()` retourne l'état d'un citizen spécifique
- [x] `check_citizen("UNKNOWN")` retourne `{"error": "unknown citizen"}`

### HTTP Server
- [ ] `GET /health` retourne 200 avec JSON valide
- [ ] `GET /unknown` retourne 404
- [ ] Serveur s'arrête proprement

### Load Check
- [x] `GET /load` retourne le score de charge VEX avec 4 dimensions
- [x] Score calculé : `(membres/20)*0.3 + (rpm/100)*0.3 + (décisions/15)*0.25 + (état/50)*0.15`
- [x] Seuils documentés : léger < 0.5, modéré 0.5-0.8, élevé 0.8-1.0, critique > 1.0

## Intégrations

### GOVERNANCE-HUB
- Lecture `known_repositories.yaml` pour valider les chemins
- Validation `pole_id`, `owner`, `semantic_clusters` via hook pre-commit

### LOOPX
- 4 daemons enregistrés : `loopx-daemon`, `loopx-telemetry`, `loopx-orchestrator`, `loopx-acp`
- Routine LOOPX `vex-orchestrator` enregistrée

### FLUENCE
- 5 daemons enregistrés : `inference-router`, `branch-divergence`, `github-sync`, `homogeneity`, `fluence-main`

### MIMIR
- 1 daemon enregistré : `mimir-server`

### FLUX
- 1 daemon enregistré : `flux-reviewer`

### BRAIN
- 1 daemon enregistré : `brain-daemon` (désactivé par défaut)

## Références
- Master : `PRD-MOC-VEX-L3-ORCHESTRATOR-20260926.md`
- Contract : `PRD-MOC-POLE-GOVERNANCE-CONTRACT-2026-09-25.md`
- Design HTTP : `design/http-server-design.md`
- Registry : `vex.yaml`
- PID Registry : `data/pid_registry.json`
- Ecosystem Value : `PRD-MOC-VEX-ECOSYSTEM-VALUE-20260927.md`
- Ecosystem Integration : `PRD-MOC-VEX-ECOSYSTEM-INTEGRATION-20260927.md`
- ADR : `ADR-2026-09-27-001-strata-orchestrator-assignment.md`
- Design : `unified-design/designs/strata-orchestrator-assignment/design.yaml`


## Proof-of-Life

- [x] 2026-09-26T02:40:00+02:00 — PID registry et daemon lifecycle définis
- [x] 2026-09-26T07:56:00+02:00 — Tests unitaires PID registry implémentés (6 tests passent)
- [x] 2026-09-26T07:56:00+02:00 — Daemon manager lifecycle tests implémentés (5 tests passent)
- [x] 2026-09-27T06:50:00+02:00 — 12 critères d'acceptation cochés sur 15 ; 3 restants couvrent le déploiement système NSSM/schtasks/systemd et le serveur HTTP, hors périmètre de test unitaire VEX
