---
type: "PRD_MOC"
version: "1.0.0"
date: "2026-09-27"
updated: "2026-09-28"
status: "implemented"
intent_hash: "0xKIX_KG-L_INTEGRATION_20260927"
parent_doc: PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER-2026-09-27.md
related_adr: ADR-2026-08-18-002-KIX-GENERIC-RUNNER-WRAPPER.md
related_moc: PRD-MOC-KIX-MASTER.md, PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER-2026-09-27.md
---

# PRD MOC - KIX - Intégration KG-L

## 1. RÉSUMÉ EXÉCUTIF

Ce PRD MOC couvre l'intégration de **KG-L** (gerivdb/KG-L) dans KIX comme runner de type `python`.

**Rôle** : Knowledge Graph, KG-L standalone
**Port** : 8888 (kg-l), 8841 (kg-l-coherence-watchdog)
**Type** : python
**Strate** : L4-TOOLS
**Statut** : ✅ **Intégré**

## 2. CONFIGURATION RUNNER

```yaml
- name: kg-l
  runner_type: python
  port: 8888
  working_dir: D:/DO/WEB/TOOLS/L4-TOOLS/KG-L
  entrypoint: src/kg_l_server.py
  depends_on: [kix]
  restart_policy: always

- name: kg-l-coherence-watchdog
  runner_type: python
  port: 8841
  working_dir: D:/DO/WEB/TOOLS/L4-TOOLS/KG-L
  entrypoint: src/kix/runtime/coherence_watchdog.py
  depends_on: [kix]
  restart_policy: always
```

## 3. RESPONSABILITÉS

| Domaine | Responsable | Description |
|---------|-------------|-------------|
| Knowledge Graph | ✅ KG-L | Stockage et requêtage graphe |
| Coherence watchdog | ✅ KG-L | Surveillance cohérence du graphe |
| Domain links | ✅ KG-L | Export `domain_links.json` |

## 4. POINTS D'INTÉGRATION KIX

| Point | Protocole | Description |
|-------|-----------|-------------|
| KIX → KG-L | REST | Health checks, requêtes graphe |
| KIX → KG-L | WAZAA Bus | Événements de mise à jour |

## 5. ENDPOINTS UTILISÉS PAR KIX

| Endpoint | Méthode | Usage KIX |
|----------|---------|-----------|
| `/health` | GET | Health check |
| `/query` | POST | Requêtes Cypher |
| `/domain_links` | GET | Export domain_links.json |

## 6. CAPABILITY MODEL

| Runner | meta.role | Capabilities |
|--------|-----------|--------------|
| kg-l | `knowledge-graph service` | `runner:start`, `runner:stop`, `health:check` |
| kg-l-coherence-watchdog | `operational` | `runner:start`, `runner:stop`, `health:check` |

## 7. GOUVERNANCE

| Attribut | Valeur |
|----------|--------|
| **Repo** | gerivdb/KG-L |
| **Local Path** | `D:\DO\WEB\TOOLS\L4-TOOLS\KG-L` |
| **ADR** | ADR-2026-08-18-002-KIX-GENERIC-RUNNER-WRAPPER.md |
| **IntentHash** | 0xKIX_KG-L_INTEGRATION_20260927 |

## 8. PREUVE-OF-LIFE

- [x] 2026-09-27T23:00:00+02:00 — Runners `kg-l` et `kg-l-coherence-watchdog` configurés
- [x] 2026-09-27T23:00:00+02:00 — PythonRunner implémenté
- [x] 2026-09-27T23:00:00+02:00 — Intégré dans PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER
- [x] 2026-09-27T23:00:00+02:00 — Capability model appliqué

## 9. RÉFÉRENCES

- `PRD-MOC-KIX-MASTER.md` : Master MOC KIX
- `PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER-2026-09-27.md` : Intégration écosystème master
- `config/runners.yaml` : Configuration runner
- `runners/python_runner.py` : Implémentation PythonRunner
- `src/kix/runtime/coherence_watchdog.py` : Coherence watchdog

---

**IntentHash** : `0xKIX_KG-L_INTEGRATION_20260927`
**Statut** : **implemented**
**Date** : 2026-09-27

*PRD-MOC-KIX-KG-L — implemented — 2026-09-27*
