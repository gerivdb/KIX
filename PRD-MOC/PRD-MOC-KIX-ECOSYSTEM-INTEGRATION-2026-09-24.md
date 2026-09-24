---
type: "PRD_MOC"
version: "1.0.0"
date: "2026-09-24"
status: "proposed"
intent_hash: "0xECOSYSTEM_INTEGRATION_MASTER_20260924"
mox_gates:
  - P-101
  - P-102
  - P-103
---

# PRD MOC - Écosystème gerivdb — Intégration Maître

## 1. RESUME EXECUTIF

Ce PRD MOC couvre l'intégration complète de l'écosystème gerivdb via KIX comme orchestrateur unique.

**Périmètre** : 70+ repos répartis en 5 couches (L0→L5)
**Objectif** : Bénéficier de l'écosystème entier via KIX : orchestration, health checks, self-healing, swarm status
**Approche** : Documentation + configuration déclarative + runners code (progressive)

## 2. ETAT ACTUEL

### 2.1 Couches et Repos

| Couche | Repos | Exemples |
|--------|-------|----------|
| L0-CANON | 6 | GOVERNANCE-HUB, unified-design, ONTOLOGY, BLO, HERMES, VERSES |
| L0-CONSTITUTIONAL | 5 | APOLLO, ARES, ATHENA, ATLAS, FORGE |
| L1_CAUSALITY | 11 | KIVA-CLI, LLM-CORE, LOOPX, ECOS-CLI, GATEWAY-MANAGER |
| L1b_INFRA | 3 | TOPOS, TQL, LLM-REPO |
| L2_PLATFORM | 20+ | KIX, PLIX, KEEL, CURX, BIRDY, EMIT, auto-dev |
| L2b_SENSOR/QUALIFIER | 3 | IRIS, KRONOS, RLM-MDU |
| L3_CITIZENS | 10+ | FLUENCE, WAZAA, LLUX, TALEX, STYX, BUZZ-X |
| L4_TOOLS | 25+ | TRIX, FLEX, KG-L, N243, CTULU, BAT-MCP, SKILLS |
| L5_ARCHIVE | 2 | localjev-upstream, archives |

### 2.2 Intégration Actuelle

| Composant | État |
|-----------|------|
| KIX orchestrateur | ✅ 100% fonctionnel |
| PythonRunner | ✅ Implémenté |
| ZigRunner | ✅ Implémenté |
| GatewayRunner | ✅ Implémenté |
| RustRunner | ❌ Manquant |
| GoRunner | ❌ Manquant |
| NodeRunner | ❌ Manquant |
| CustomRunner | ❌ Manquant |
| Documentation écosystème | ⚠️ Partielle |

## 3. ARCHITECTURE CIBLE

### 3.1 Principe Fondateur

**KIX est l'orchestrateur unique de tous les services applicatifs de l'écosystème gerivdb**.

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
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐       │   │
│  │  │ python │ │ zig    │ │ rust   │ │ go     │ ...   │   │
│  │  └────────┘ └────────┘ └────────┘ └────────┘       │   │
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

### 3.2 Types de Runners

| Type | Langage | Binaire/Commande | Repos Cibles |
|------|---------|------------------|--------------|
| `python` | Python | `python <entrypoint>` | KIX, GATEWAY-MANAGER, WAZAA, FLEX |
| `zig-binary` | Zig | `zig-out/bin/<binary>` | TRIX, LLUX, ROOTX |
| `gateway-exe` | Exe/CLI | `<binary>` | GATEWAY-MANAGER, BAT-MCP |
| `rust` | Rust | `cargo run --bin <name>` | FLEX, OBSCURA, TRIX |
| `go` | Go | `go run .` | Services Go |
| `node` | Node.js | `node server.js` | Services Node |
| `custom` | Custom | commande arbitraire | Tous |

## 4. PLAN D'IMPLEMENTATION

### Phase 1 : Documentation (Semaine 1) — EN COURS
- [x] Créer PRD MOC écosystème
- [x] Créer ADR intégration multi-langages
- [x] Créer docs/ecosystem-integration.md
- [x] Mettre à jour runners.yaml avec stubs
- [ ] Valider gates MOX P-101/P-102/P-103

### Phase 2 : Rust/Go/Node Runners (Semaines 2-3)
- [ ] Créer `runners/rust_runner.py`
- [ ] Créer `runners/go_runner.py`
- [ ] Créer `runners/node_runner.py`
- [ ] Créer `runners/custom_runner.py`
- [ ] Ajouter dans `registry.py`
- [ ] Tests unitaires

### Phase 3 : Intégration Complète (Semaines 4-6)
- [ ] Enrôler tous les repos SOT dans runners.yaml
- [ ] Tester chaque runner en environnement local
- [ ] Mettre à jour documentation
- [ ] Valider opérationnel 100%

## 5. DEPENDANCES

### 5.1 Internes
- `KIX/runners/base.py` : interface `RunnerBase`
- `KIX/runners/registry.py` : registry des runners
- `KIX/config/runners.yaml` : configuration déclarative
- `KIX/libs/shared-clients/win32_process.py` : primitives Win32
- `GOVERNANCE-HUB/known_repositories.yaml` : SOT des repos

### 5.2 Externes
- `C:\DevTools\.cargo\bin\rustc.exe` : Rust
- `C:\DevTools\.cargo\bin\cargo.exe` : Rust
- `C:\DevTools\go\` : Go (à installer)
- `node.exe` : Node.js (à vérifier)

## 6. TRACABILITE

### 6.1 Thought Chain

```yaml
thought_chain:
  - source: "Observation : 70+ repos gerivdb non orchestrés par KIX"
    artifact: "Nécessité d'intégration écosystème complète"
    intent_hash: "0xECOSYSTEM_INTEGRATION_MASTER_20260924"
```

### 6.2 Gates

| Gate | Critère | Statut |
|------|---------|--------|
| **P-101** | Conformité schéma YAML | ⏳ PENDING |
| **P-102** | Forward references valides | ⏳ PENDING |
| **P-103** | Tests unitaires ≥ 80% | ⏸️ BLOCKED |

## 7. REFERENCES

- `PRD-MOC-KIX-ORCHESTRATOR-2026-08-18.md` : PRD MOC KIX orchestrateur
- `PRD-MOC-KIX-MASTER.md` : Master MOC KIX
- `PRD-MOC-KIX-MULTI-LANG-ECOSYSTEM-2026-09-24.md` : Intégration multi-langages
- `ADR-2026-09-24-KIX-MULTI-LANG-RUNNERS.md` : ADR runners
- `GOVERNANCE-HUB/known_repositories.yaml` : SOT des repos
