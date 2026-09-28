---
type: "PRD_MOC"
version: "1.0.0"
date: "2026-09-28"
updated: "2026-09-28"
status: "implemented"
intent_hash: "0xKIX_AGENT_MANAGER_INTEGRATION_20260928"
parent_doc: PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER-2026-09-27.md
related_adr: ADR-2026-08-18-002-KIX-GENERIC-RUNNER-WRAPPER.md
related_moc: PRD-MOC-KIX-MASTER.md, PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER-2026-09-27.md
---

# PRD MOC - KIX - Intégration Agent Manager

## 1. RÉSUMÉ EXÉCUTIF

Ce PRD MOC couvre l'intégration de **Agent Manager** dans KIX comme runner de type `gateway-exe`.

**Rôle** : Agent Manager
**Port** : 18001
**Type** : gateway-exe
**Strate** : L1-INFRA
**Statut** : ✅ **Intégré**

## 2. CONFIGURATION RUNNER

```yaml
- name: agent-manager
  runner_type: gateway-exe
  port: 18001
  working_dir: D:/DO/WEB/TOOLS/L1-INFRA/AGENT-MANAGER
  depends_on: [kix]
  meta:
    repo: gerivdb/KIX
    role: orchestrator
  binary: agent-manager.exe
```

## 3. RESPONSABILITÉS

| Domaine | Responsable | Description |
|---------|-------------|-------------|
| Orchestration agents | ✅ Agent Manager | Sessions parallèles et worktrees |
| Budget RAM/CPU | ✅ Agent Manager | Contrôle des sessions concurrentes |
| Assignments | ✅ Agent Manager | Sections et sessions Manager |

## 4. POINTS D'INTÉGRATION KIX

| Point | Protocole | Description |
|-------|-----------|-------------|
| KIX → Agent Manager | REST | Health checks, orchestration |
| bootstrap → Agent Manager | HTTP | Vérification dépendance |

## 5. ENDPOINTS UTILISÉS PAR KIX

| Endpoint | Méthode | Usage KIX |
|----------|---------|-----------|
| `/health` | GET | Health check |

## 6. CAPABILITY MODEL

| Runner | meta.role | Capabilities |
|--------|-----------|--------------|
| agent-manager | `orchestrator` | `runner:start`, `runner:stop`, `health:check` |

## 7. GOUVERNANCE

| Attribut | Valeur |
|----------|--------|
| **Repo** | gerivdb/KIX |
| **Local Path** | `D:\DO\WEB\TOOLS\L1-INFRA\AGENT-MANAGER` |
| **ADR** | ADR-2026-08-18-002-KIX-GENERIC-RUNNER-WRAPPER.md |
| **IntentHash** | 0xKIX_AGENT_MANAGER_INTEGRATION_20260928 |

## 8. PREUVE-OF-LIFE

- [x] 2026-09-28T02:45:00+02:00 — Runner `agent-manager` documenté dans `runners.yaml`
- [x] 2026-09-28T02:45:00+02:00 — GatewayRunner implémenté dans `runners/gateway_runner.py`
- [x] 2026-09-28T02:45:00+02:00 — Intégré dans PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER

## 9. RÉFÉRENCES

- `PRD-MOC-KIX-MASTER.md` : Master MOC KIX
- `PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER-2026-09-27.md` : Intégration écosystème master
- `config/runners.yaml` : Configuration runner
- `runners/gateway_runner.py` : Implémentation GatewayRunner

---

**IntentHash** : `0xKIX_AGENT_MANAGER_INTEGRATION_20260928`
**Statut** : **implemented**
**Date** : 2026-09-28

*PRD-MOC-KIX-AGENT-MANAGER — implemented — 2026-09-28*
