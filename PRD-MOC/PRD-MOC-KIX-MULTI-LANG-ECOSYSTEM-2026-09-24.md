---
type: "PRD_MOC"
version: "1.0.0"
date: "2026-09-24"
status: "proposed"
intent_hash: "0xKIX_MULTI_LANG_ECOSYSTEM_20260924"
mox_gates:
  - P-101
  - P-102
  - P-103
---

# PRD MOC - KIX - Intégration Multi-Langages et Écosystème

## 1. RESUME EXECUTIF

Ce PRD MOC complète `PRD-MOC-KIX-ORCHESTRATOR-2026-08-18.md` et `PRD-MOC-KIX-MASTER.md` pour couvrir :
- L'intégration réelle des runners **Rust**, **Go**, **Node** dans KIX
- L'utilisation de l'écosystème entier des repos gerivdb via KIX
- La gestion des processus système `python.exe`, `rust.exe`, `go.exe`, `node.exe`

**Constat d'écart** :
- `runners/base.py` déclare les types `rust|node|custom`
- `runners/registry.py` n'implémente que `python|zig-binary|gateway-exe`
- Aucun runner `rust` ou `go` n'existe dans `runners/`
- Aucun exécutable Go n'est installé dans `C:\DevTools`

## 2. ETAT ACTUEL

### 2.1 Runners Implémentés

| Runner Type | Fichier | Statut |
|-------------|---------|--------|
| `python` | `runners/python_runner.py` | ✅ IMPLEMENTÉ |
| `zig-binary` | `runners/zig_runner.py` | ✅ IMPLEMENTÉ |
| `gateway-exe` | `runners/gateway_runner.py` | ✅ IMPLEMENTÉ |
| `rust` | `runners/rust_runner.py` | ❌ MANQUANT |
| `go` | `runners/go_runner.py` | ❌ MANQUANT |
| `node` | `runners/node_runner.py` | ❌ MANQUANT |
| `custom` | `runners/custom_runner.py` | ❌ MANQUANT |

### 2.2 Outils Système Disponibles

| Outil | Chemin | Statut |
|-------|--------|--------|
| `python.exe` | `C:\Users\GG\AppData\Local\Programs\Python\Python312\python.exe` | ✅ DISPONIBLE |
| `rustc.exe` | `C:\DevTools\.cargo\bin\rustc.exe` | ✅ DISPONIBLE |
| `cargo.exe` | `C:\DevTools\.cargo\bin\cargo.exe` | ✅ DISPONIBLE |
| `go.exe` | `C:\DevTools\bin\go\` | ❌ DOSSIER VIDE |
| `node.exe` | Via `npm`/`npx` | ✅ DISPONIBLE |

### 2.3 Documentation Existante

| Document | Couverture | Gap |
|----------|-----------|-----|
| `PRD-MOC-KIX-ORCHESTRATOR-2026-08-18.md` | Python/Zig/Gateway | Pas Rust/Go |
| `PRD-MOC-KIX-MASTER.md` | Vue d'ensemble KIX | Pas d'intégration écosystème |
| `config/runners.yaml` | 5 runners | Pas de runners Rust/Go |

## 3. ARCHITECTURE CIBLE

### 3.1 Principe

**KIX est l'orchestrateur unique de tous les services applicatifs de l'écosystème gerivdb**, tous langages confondus.

- `RunnerBase` étendu pour supporter `rust`, `go`, `node`, `custom`
- `runners.yaml` comme registry déclaratif unique
- `win32_process.py` comme couche système commune
- Health checks, logs, restart policy identiques pour tous les types

### 3.2 Nouveaux Runners Cibles

| Runner Type | Binaire/Commande | Usage |
|-------------|------------------|-------|
| `rust` | `cargo run --bin <name>` ou binaire compilé | Services Rust (FLEX, TRIX, etc.) |
| `go` | `go run .` ou binaire compilé | Services Go |
| `node` | `node server.js` ou `npm start` | Services Node.js |
| `custom` | Commande arbitraire | Tout service non standard |

## 4. PLAN D'IMPLEMENTATION

### Phase 1 : Rust Runner
- Créer `runners/rust_runner.py`
- Ajouter le runner dans `registry.py`
- Tests unitaires

### Phase 2 : Go Runner
- Installer Go dans `C:\DevTools\go\`
- Créer `runners/go_runner.py`
- Ajouter le runner dans `registry.py`
- Tests unitaires

### Phase 3 : Node/Custom Runners
- Créer `runners/node_runner.py`
- Créer `runners/custom_runner.py`
- Ajouter dans `registry.py`

### Phase 4 : Documentation Écosystème
- Mettre à jour `PRD-MOC-KIX-MASTER.md`
- Créer `docs/ecosystem-integration.md`
- Mettre à jour `runners.yaml` avec tous les runners

## 5. DEPENDANCES

### 5.1 Internes
- `KIX/libs/shared-clients/win32_process.py` : primitives Win32
- `KIX/runners/base.py` : interface `RunnerBase`
- `KIX/config/runners.yaml` : registry déclaratif

### 5.2 Externes
- `C:\DevTools\.cargo\bin\rustc.exe` : compilateur Rust
- `C:\DevTools\.cargo\bin\cargo.exe` : gestionnaire de paquets Rust
- Go : à installer dans `C:\DevTools\go\`
- Node.js : à vérifier dans `C:\DevTools\node\`

## 6. TRACABILITE

### 6.1 Thought Chain

```yaml
thought_chain:
  - source: "Observation : Rust/Go absents de runners.yaml malgré déclaration dans base.py"
    artifact: "Gap documentation + implémentation"
    intent_hash: "0xKIX_MULTI_LANG_ECOSYSTEM_20260924"
```

### 6.2 Gates

| Gate | Critère | Statut |
|------|---------|--------|
| **P-101** | Conformité schéma YAML | ⏳ PENDING |
| **P-102** | Forward references valides | ⏳ PENDING |
| **P-103** | Tests unitaires ≥ 80% | ⏸️ BLOCKED |

## 7. REFERENCES

- `PRD-MOC-KIX-ORCHESTRATOR-2026-08-18.md` : PRD MOC existant
- `PRD-MOC-KIX-MASTER.md` : Master MOC KIX
- `ADR-2026-07-27-002-KIX.md` : ADR initiale KIX
- `config/runners.yaml` : Configuration déclarative
- `runners/base.py` : Interface `RunnerBase`
