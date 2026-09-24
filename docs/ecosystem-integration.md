# KIX - Intégration Écosystème

## Vue d'Ensemble

KIX est l'orchestrateur unique de tous les services applicatifs DevTools/ENV2, tous langages confondus.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Agent Manager / N+2/N+3               │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                          KIX (port 8800)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  RunnerBase │  │  Registry   │  │  Doctor     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│         │                │                │                 │
│         ▼                ▼                ▼                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              runners.yaml (déclaratif)               │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│ PythonRunner │      │ ZigRunner    │      │ RustRunner   │
│ .py          │      │ .exe         │      │ cargo/rustc  │
├──────────────┤      ├──────────────┤      ├──────────────┤
│ GoRunner     │      │ GatewayRunner│      │ NodeRunner   │
│ go run .     │      │ .exe/CLI     │      │ node server  │
└──────────────┘      └──────────────┘      └──────────────┘
```

## Services Gérés par KIX

### Python Services

| Runner | Port | Repo | Rôle |
|--------|------|------|------|
| kix | 8800 | gerivdb/KIX | Orchestrateur |
| gateway-manager | 8802 | gerivdb/GATEWAY-MANAGER | Proxy/Clapet |
| kg-l | 8888 | gerivdb/KG-L | Knowledge Graph |
| wazaa | 1873 | gerivdb/WAZAA | Bus événementiel |
| flex-api | 7719 | gerivdb/FLEX | Cache/Flex |

### Zig Services

| Runner | Port | Repo | Rôle |
|--------|------|------|------|
| trixd | 7243 | gerivdb/TRIX | Runtime Zig |

### Rust Services (à implémenter)

| Runner | Port | Repo | Rôle |
|--------|------|------|------|
| flex-rust | 7718 | gerivdb/FLEX | Service Rust |

### Go Services (à installer/implémenter)

| Runner | Port | Repo | Rôle |
|--------|------|------|------|
| go-service | 7717 | gerivdb/GO-SERVICE | Service Go |

### Node Services (à implémenter)

| Runner | Port | Repo | Rôle |
|--------|------|------|------|
| node-service | 7716 | gerivdb/NODE-SERVICE | Service Node.js |

## API REST KIX

### Endpoints Disponibles

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
| `/readyz` | GET | Readiness probe |
| `/doctor` | GET | Vérifie tous les runners |
| `/doctor/run` | POST | Redémarre les runners en erreur |
| `/swarm/status` | GET | État agrégé pour Agent Manager |

### Exemples d'Usage

```bash
# Démarrer tous les runners
curl -X POST http://localhost:8800/runners/kix/start

# Vérifier le status d'un runner
curl http://localhost:8800/runners/trixd/status

# Health check global
curl http://localhost:8800/health

# Doctor : vérifier tous les runners
curl http://localhost:8800/doctor

# Auto-redémarrage des runners en erreur
curl -X POST http://localhost:8800/doctor/run

# Swarm status pour Agent Manager
curl http://localhost:8800/swarm/status
```

## Configuration Déclarative

### runners.yaml

Tous les runners sont définis dans `config/runners.yaml`. Exemple :

```yaml
runners:
  - name: trixd
    runner_type: zig-binary
    port: 7243
    working_dir: D:/DO/WEB/TOOLS/L4-TOOLS/TRIX
    binary: zig-out/bin/trixd.exe
    build:
      command: ["zig", "build", "trixd"]
      required: true
      pre_start: true
    depends_on:
      - kix
    health_path: /health
    restart_policy: on-failure
    meta:
      repo: gerivdb/TRIX
      role: zig runtime
```

### Types de Runners

| Type | Usage | Exemple |
|------|-------|---------|
| `python` | Services Python | `python src/app.py` |
| `zig-binary` | Binaires Zig | `trixd.exe` |
| `gateway-exe` | Executables/CLI | `gateway-manager.exe` |
| `rust` | Services Rust | `cargo run --bin flex-api` |
| `go` | Services Go | `go run .` |
| `node` | Services Node.js | `node server.js` |
| `custom` | Commandes arbitraires | `custom_cmd --arg` |

## Gestion des Processus

### Processus Attendus

KIX gère les processus suivants via `win32_process.py` :

| Langage | Processus | Géré par |
|---------|-----------|----------|
| Python | `python.exe` | `PythonRunner` |
| Rust | `rustc.exe`, `cargo.exe` | `RustRunner` |
| Go | `go.exe` | `GoRunner` |
| Node | `node.exe` | `NodeRunner` |
| Zig | `trixd.exe` | `ZigBinaryRunner` |

### Zombie Monitor

KIX inclut un `zombie_monitor.py` qui détecte :
- Processus zombies
- Worktrees orphelins
- Stashes anciens

## Intégration Écosystème

### Repos Gérés

| Repo | Strate | Service | Port |
|------|--------|---------|------|
| gerivdb/KIX | L2-PLATFORM | Orchestrateur | 8800 |
| gerivdb/GATEWAY-MANAGER | L1-INFRA | Proxy/Clapet | 8802 |
| gerivdb/TRIX | L4-TOOLS | Runtime Zig | 7243 |
| gerivdb/WAZAA | L4-TOOLS | Bus événementiel | 1873 |
| gerivdb/FLEX | L4-TOOLS | Cache/Flex | 7719 |
| gerivdb/KG-L | L4-TOOLS | Knowledge Graph | 8888 |
| gerivdb/JEVX | L4-TOOLS | Decision Engine | 8889 |

### Cross-Repo Dependencies

| Source | Cible | Type |
|--------|-------|------|
| KIX → GATEWAY-MANAGER | Orchestration → Proxy | REST + WAZAA |
| KIX → TRIX | Orchestration → Runtime | REST + WAZAA |
| KIX → WAZAA | Orchestration → Bus | WAZAA Bus |
| KIX → FLEX | Orchestration → Cache | REST + WAZAA |

## Gouvernance

### ADR Références

- ADR-2026-07-27-002-KIX : ADR initiale KIX
- ADR-2026-09-24-KIX-MULTI-LANG-RUNNERS : Support multi-langages

### PRD MOC Références

- PRD-MOC-KIX-ORCHESTRATOR-2026-08-18.md : PRD MOC orchestrateur
- PRD-MOC-KIX-MASTER.md : Master MOC KIX
- PRD-MOC-KIX-MULTI-LANG-ECOSYSTEM-2026-09-24.md : Intégration multi-langages

### Gates MOX

| Gate | Critère | Statut |
|------|---------|--------|
| P-101 | Conformité schéma YAML | ⏳ PENDING |
| P-102 | Forward references valides | ⏳ PENDING |
| P-103 | Tests unitaires ≥ 80% | ⏸️ BLOCKED |
