---
type: "PRD_MOC"
version: "1.0.0"
date: "2026-09-27"
updated: "2026-09-28"
status: "implemented"
intent_hash: "0xKIX_JEVX_INTEGRATION_20260927"
parent_doc: PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER-2026-09-27.md
related_adr: ADR-2026-08-18-002-KIX-GENERIC-RUNNER-WRAPPER.md, ADR-2026-09-24-KIX-MULTI-LANG-RUNNERS.md
related_moc: PRD-MOC-KIX-MASTER.md, PRD-MOC-KIX-MULTI-LANG-ECOSYSTEM-2026-09-24.md
---

# PRD MOC - KIX - Intégration JEVX

## 1. RÉSUMÉ EXÉCUTIF

Ce PRD MOC couvre l'intégration de **JEVX** (gerivdb/JEVX) dans KIX comme runner de type `node`.

**Rôle** : Decision-engine -- Surcouche souveraine sur upstream LocalJev
**Port** : 8889
**Type** : node
**Strate** : L4-TOOLS
**Statut** : ✅ **Intégré**

## 2. CONFIGURATION RUNNER

```yaml
- name: jevx
  runner_type: node
  port: 8889
  working_dir: D:/DO/WEB/TOOLS/L4-TOOLS/JEVX
  entrypoint: server.js
  depends_on: [kix]
  restart_policy: always
```

## 3. RESPONSABILITÉS

| Domaine | Responsable | Description |
|---------|-------------|-------------|
| Decision Engine | ✅ JEVX | Moteur de décision souverain |
| LocalJev wrapper | ✅ JEVX | Surcouche sur upstream LocalJev |

## 4. POINTS D'INTÉGRATION KIX

| Point | Protocole | Description |
|-------|-----------|-------------|
| KIX → JEVX | REST | Health checks, décisions |
| bootstrap → JEVX | HTTP | Vérification dépendance |

## 5. ENDPOINTS UTILISÉS PAR KIX

| Endpoint | Méthode | Usage KIX |
|----------|---------|-----------|
| `/health` | GET | Health check |
| `/decide` | POST | Requêtes de décision |

## 6. CAPABILITY MODEL

| Runner | meta.role | Capabilities |
|--------|-----------|--------------|
| jevx | `decision-engine` | `runner:start`, `runner:stop`, `health:check` |

## 7. GOUVERNANCE

| Attribut | Valeur |
|----------|--------|
| **Repo** | gerivdb/JEVX |
| **Local Path** | `D:\DO\WEB\TOOLS\L4-TOOLS\JEVX` |
| **ADR** | ADR-2026-09-24-KIX-MULTI-LANG-RUNNERS.md |
| **IntentHash** | 0xKIX_JEVX_INTEGRATION_20260927 |

## 8. PREUVE-OF-LIFE

- [x] 2026-09-27T23:00:00+02:00 — Runner `jevx` configuré dans `runners.yaml`
- [x] 2026-09-27T23:00:00+02:00 — NodeRunner implémenté dans `runners/node_runner.py`
- [x] 2026-09-27T23:00:00+02:00 — Intégré dans PRD-MOC-KIX-MULTI-LANG-ECOSYSTEM
- [x] 2026-09-27T23:00:00+02:00 — Capability model appliqué

## 9. RÉFÉRENCES

- `PRD-MOC-KIX-MASTER.md` : Master MOC KIX
- `PRD-MOC-KIX-MULTI-LANG-ECOSYSTEM-2026-09-24.md` : Multi-lang ecosystem
- `config/runners.yaml` : Configuration runner
- `runners/node_runner.py` : Implémentation NodeRunner

---

**IntentHash** : `0xKIX_JEVX_INTEGRATION_20260927`
**Statut** : **implemented**
**Date** : 2026-09-27

*PRD-MOC-KIX-JEVX — implemented — 2026-09-27*
