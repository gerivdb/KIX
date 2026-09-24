---
type: ADR
status: proposed
date: "2026-09-24"
intent_hash: 0xADR_ECOSYSTEM_INTEGRATION_20260924
---

# ADR - KIX - Intégration Écosystème gerivdb

## Contexte

L'écosystème gerivdb comprend 70+ repos répartis en 5 couches (L0→L5). Ces repos sont actuellement orchestrés manuellement ou via des scripts ad-hoc :

- **L0-CANON** : GOVERNANCE-HUB, unified-design, ONTOLOGY, BLO, HERMES, VERSES
- **L1_CAUSALITY** : KIVA-CLI, LLM-CORE, LOOPX, ECOS-CLI, GATEWAY-MANAGER
- **L2_PLATFORM** : KIX, PLIX, KEEL, CURX, BIRDY, EMIT, auto-dev
- **L3_CITIZENS** : FLUENCE, WAZAA, LLUX, TALEX, STYX, BUZZ-X
- **L4_TOOLS** : TRIX, FLEX, KG-L, N243, CTULU, BAT-MCP, SKILLS

KIX est l'orchestrateur central, mais il ne gère actuellement que 5 runners. L'intégration complète de l'écosystème nécessite :
1. Des runners pour tous les langages (Python, Zig, Rust, Go, Node)
2. Une configuration déclarative de tous les services
3. Une documentation écosystème complète

## Décision

Étendre KIX pour devenir l'orchestrateur unique de TOUS les services applicatifs de l'écosystème gerivdb :

### Architecture Cible

```
KIX (port 8800)
├── RunnerBase (interface unifiée)
│   ├── PythonRunner
│   ├── ZigBinaryRunner
│   ├── GatewayRunner
│   ├── RustRunner (nouveau)
│   ├── GoRunner (nouveau)
│   ├── NodeRunner (nouveau)
│   └── CustomRunner (nouveau)
├── Registry (runners.yaml)
│   ├── 70+ runners déclaratifs
│   └── Dépendances, health checks, restart policies
├── Doctor/Self-Healing
│   ├── Health checks parallélisés
│   ├── Auto-redémarrage
│   └── Swarm Status
└── API REST
    ├── /runners (liste + status)
    ├── /runners/{name}/start|stop|restart|health|logs
    ├── /doctor (vérification)
    ├── /doctor/run (auto-redémarrage)
    └── /swarm/status (état agrégé)
```

### Principes

1. **Uniformisation** : tous les services, tous langages, via la même API REST KIX
2. **Déclaratif** : `runners.yaml` comme registry unique, zéro logique en dur
3. **Résilient** : Doctor/Self-Healing intégré, health checks parallélisés
4. **Évolutif** : ajout d'un runner = ajout dans `runners.yaml` + classe Runner si nouveau type
5. **Traçable** : WAL, logs, métriques pour chaque runner

## Implications

### Techniques
- **Code** : créer 4 runners manquants (Rust, Go, Node, Custom)
- **Config** : mettre à jour `runners.yaml` avec 70+ entrées
- **Tests** : tests unitaires pour chaque nouveau runner
- **Health checks** : parallélisation via ThreadPoolExecutor

### Organisationnelles
- **Documentation** : créer `docs/ecosystem-integration.md`
- **Gouvernance** : PRD MOC + ADR + INTENTS pour chaque phase
- **Formation** : les équipes utilisent KIX au lieu de scripts ad-hoc

### Opérationnelles
- **Démarrage** : KIX démarre tous les services via `/runners/{name}/start`
- **Monitoring** : `/doctor` vérifie tous les runners
- **Self-Healing** : `/doctor/run` redémarre les runners en erreur
- **Swarm** : `/swarm/status` pour Agent Manager/N+2/N+3

## Alternatives

| Alternative | Raison Rejet |
|-------------|--------------|
| Garder le status quo | Orphelins, pas de health checks, pas de self-healing |
| Créer un orchestrateur par couche | Duplication, complexité, perte de vue unifiée |
| Utiliser des scripts ad-hoc | Pas de traçabilité, pas de résilience, pas de standardisation |
| Utiliser un outil externe (systemd, supervisord) | Pas d'intégration écosystème, pas de WAL, pas de swarm status |

## Statut

- **Repo** : `gerivdb/KIX`
- **Port** : 8800
- **IntentHash** : `0xADR_ECOSYSTEM_INTEGRATION_20260924`
- **Dépendances** : `runners/base.py`, `config/runners.yaml`, `libs/shared-clients/win32_process.py`
- **Bloqueurs** : Go non installé, runners Rust/Go/Node/Custom non implémentés

## Rollback

Si l'intégration écosystème échoue :
1. Revenir à `runners.yaml` avec 5 runners seulement
2. Supprimer les runners Rust/Go/Node/Custom
3. Garder KIX fonctionnel pour les runners existants
4. Aucun impact sur les services existants
