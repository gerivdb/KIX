# KIX - Guide d'Intégration Écosystème

## Vue d'Ensemble

KIX est l'orchestrateur unique de tous les services applicatifs de l'écosystème gerivdb (70+ repos, L0→L5).

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    KIX (port 8800)                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  RunnerBase │  │  Registry   │  │  Doctor     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
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
│ L0-CANON     │      │ L2-PLATFORM  │      │ L4-TOOLS     │
│ GOVERNANCE   │      │ KIX, PLIX    │      │ TRIX, FLEX   │
│ ONTOLOGY     │      │ KEEL, CURX   │      │ KG-L, N243   │
│ BLO, HERMES  │      │ BIRDY, EMIT  │      │ WAZAA, TALEX │
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
| kix-ecosystem | 8811 | gerivdb/KIX | Ecosystem orchestrator |

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

## Intégration Écosystème

### Repos Gérés

| Repo | Strate | Service | Port | Type |
|------|--------|---------|------|------|
| gerivdb/KIX | L2-PLATFORM | Orchestrateur | 8800 | python |
| gerivdb/GATEWAY-MANAGER | L1-INFRA | Proxy/Clapet | 8802 | gateway-exe |
| gerivdb/TRIX | L4-TOOLS | Runtime Zig | 7243 | zig-binary |
| gerivdb/WAZAA | L4-TOOLS | Bus événementiel | 1873 | python |
| gerivdb/FLEX | L4-TOOLS | Cache/Flex | 7719 | python |
| gerivdb/KG-L | L4-TOOLS | Knowledge Graph | 8888 | python |
| gerivdb/JEVX | L4-TOOLS | Decision Engine | 8889 | service |
| gerivdb/BAT-MCP | L4-TOOLS | MCP Gateway | 8000 | gateway-exe |

### Cross-Repo Dependencies

| Source | Cible | Type |
|--------|-------|------|
| KIX → GATEWAY-MANAGER | Orchestration → Proxy | REST + WAZAA |
| KIX → TRIX | Orchestration → Runtime | REST + WAZAA |
| KIX → WAZAA | Orchestration → Bus | WAZAA Bus |
| KIX → FLEX | Orchestration → Cache | REST + WAZAA |
| KIX → KG-L | Orchestration → Knowledge Graph | REST |
| KIX → JEVX | Orchestration → Decision Engine | REST |

## Gouvernance

### ADR Références

- ADR-2026-07-27-002-KIX : ADR initiale KIX
- ADR-2026-09-24-KIX-MULTI-LANG-RUNNERS : Support multi-langages
- ADR-2026-09-24-ECOSYSTEM-INTEGRATION : Intégration écosystème

### PRD MOC Références

- PRD-MOC-KIX-ORCHESTRATOR-2026-08-18.md : PRD MOC orchestrateur
- PRD-MOC-KIX-MASTER.md : Master MOC KIX
- PRD-MOC-KIX-MULTI-LANG-ECOSYSTEM-2026-09-24.md : Intégration multi-langages
- PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER-2026-09-27.md : Intégration écosystème master
- PRD-MOC-KIX-BOOTSTRAP-RUNNER-2026-08-20.md : Bootstrap runner
- PRD-MOC-KIX-EXE-ORCHESTRATION-2026-09-24.md : Exe orchestration / preflight / zombie monitor
- PRD-MOC-VEX-KIX-BOUNDARIES-20260927.md : Frontières KIX/VEX

### Gates MOX

| Gate | Critère | Statut |
|------|---------|--------|
| **P-301** | Schéma YAML `runners.yaml` valide | ✅ VALIDÉ |
| **P-302** | Forward references valides | ✅ VALIDÉ |
| **P-303** | Tous runners référencés existent | ✅ VALIDÉ |
| **P-304** | Endpoints `/bootstrap/*` fonctionnels | ✅ VALIDÉ |
| **P-305** | ECOS CLI integration testée | ✅ VALIDÉ |
| **P-306** | WAZAA bus connectivity | ✅ VALIDÉ |

## État Actuel (2026-09-27)

- 60 runners déclaratifs dans `config/runners.yaml`
- 23 runners actifs (`auto_start`)
- 7 types de runners implémentés (`python`, `gateway-exe`, `zig-binary`, `rust`, `go`, `node`, `custom`)
- Bootstrap runner opérationnel sur port 8810
- KIX opérationnel sur port 8800
- ECOS CLI integration validée
- WAZAA bus opérationnel sur port 1873

## Prochaines Étapes

1. **Pérenniser l'intégration** : maintenir `runners.yaml` à jour avec la SOT
2. **Étendre les runners actifs** : activer les runners custom selon besoin opérationnel
3. **Améliorer la couverture de tests** : ajouter des tests d'intégration par runner
4. **Surveillance** : exploiter `/doctor`, `/swarm/status`, `/bootstrap/monitor`
5. **Documentation** : maintenir ce guide et les PRD MOC à jour
