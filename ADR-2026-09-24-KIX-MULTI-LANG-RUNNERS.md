---
type: ADR
status: proposed
date: "2026-09-24"
intent_hash: 0xADR_KIX_MULTI_LANG_20260924
---

# ADR - KIX - Support Multi-Langages Rust/Go/Node

## Contexte

KIX est l'orchestrateur central des services applicatifs DevTools/ENV2. Le `runners/base.py` déclare les types `rust|node|custom`, mais seuls `python|zig-binary|gateway-exe` sont implémentés dans `registry.py`. 

De plus :
- Rust est disponible dans `C:\DevTools\.cargo\bin\`
- Go n'est pas installé dans `C:\DevTools\`
- Plusieurs services de l'écosystème gerivdb pourraient bénéficier d'un orchestreur unifié

## Décision

Étendre KIX pour supporter tous les langages de l'écosystème via des runners dédiés :

| Langage | Runner | Binaire/Commande |
|---------|--------|------------------|
| Python | `PythonRunner` | `python <entrypoint>` |
| Zig | `ZigBinaryRunner` | `zig-out/bin/<binary>` |
| Gateway | `GatewayRunner` | `.exe`/CLI |
| Rust | `RustRunner` | `cargo run --bin <name>` |
| Go | `GoRunner` | `go run .` |
| Node | `NodeRunner` | `node server.js` |
| Custom | `CustomRunner` | commande arbitraire |

## Implications

- **Uniformisation** : tous les services, tous langages, via la même API REST KIX
- **Doctor/Self-Healing** : health checks parallélisés pour tous les runners
- **Swarm Status** : vue agrégée pour Agent Manager/N+2/N+3
- **Écosystème** : KIX devient le point d'entrée unique pour l'orchestration DevTools/ENV2
- **Go manquant** : nécessite installation de Go dans `C:\DevTools\go\`

## Alternatives

| Alternative | Raison Rejet |
|-------------|--------------|
| Garder le status quo | Gap documentation + impossibilité d'orchestrer Rust/Go |
| Créer un orchestrateur séparé | Duplication, complexité, perte de vue unifiée |
| Utiliser des scripts ad-hoc | Pas de health checks, pas de self-healing, pas de traçabilité |

## Statut

- **Repo** : `gerivdb/KIX`
- **Port** : 8800
- **IntentHash** : `0xADR_KIX_MULTI_LANG_20260924`
- **Dépendances** : `runners/base.py`, `config/runners.yaml`, `libs/shared-clients/win32_process.py`
