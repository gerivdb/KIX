---
type: "PRD_MOC"
version: "1.0.0"
date: "2026-09-28"
updated: "2026-09-28"
status: "implemented"
intent_hash: "0xKIX_BATMCP_INTEGRATION_20260928"
parent_doc: PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER-2026-09-27.md
related_adr: ADR-2026-08-18-002-KIX-GENERIC-RUNNER-WRAPPER.md
related_moc: PRD-MOC-KIX-MASTER.md, PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER-2026-09-27.md
---

# PRD MOC - KIX - Intégration BatMCP

## 1. RÉSUMÉ EXÉCUTIF

Ce PRD MOC couvre l'intégration de **BatMCP** (gerivdb/BatMCP) dans KIX comme runner de type `gateway-exe`.

**Rôle** : Serveur MCP, outils batch
**Port** : 8000
**Type** : gateway-exe
**Strate** : L4-TOOLS
**Statut** : ✅ **Intégré**

## 2. CONFIGURATION RUNNER

```yaml
- name: batmcp
  runner_type: gateway-exe
  port: 8000
  working_dir: D:/DO/WEB/TOOLS/L4-TOOLS/BatMCP
  command: ['python', '-m', 'uvicorn', 'src.server:app', '--host', 'localhost', '--port', '8000']
  depends_on: [kix]
  health_path: /health
  restart_policy: on-failure
  log_file: D:/DO/WEB/TOOLS/L4-TOOLS/BatMCP/logs/batmcp.log
  pid_file: D:/DO/WEB/TOOLS/L4-TOOLS/BatMCP/logs/batmcp.pid
  meta:
    repo: gerivdb/BatMCP
    role: mcp-server
  binary: batmcp.exe
```

## 3. RESPONSABILITÉS

| Domaine | Responsable | Description |
|---------|-------------|-------------|
| Serveur MCP | ✅ BatMCP | Outils MCP pour batch |
| API REST | ✅ BatMCP | Endpoints MCP |
| Health checks | ✅ KIX | Surveillance via `/health` |

## 4. POINTS D'INTÉGRATION KIX

| Point | Protocole | Description |
|-------|-----------|-------------|
| KIX → BatMCP | REST + WAZAA | Health checks, orchestration |
| bootstrap → BatMCP | HTTP | Vérification dépendance |

## 5. ENDPOINTS UTILISÉS PAR KIX

| Endpoint | Méthode | Usage KIX |
|----------|---------|-----------|
| `/health` | GET | Health check |

## 6. CAPABILITY MODEL

| Runner | meta.role | Capabilities |
|--------|-----------|--------------|
| batmcp | `mcp-server` | `runner:start`, `runner:stop`, `health:check` |

## 7. GOUVERNANCE

| Attribut | Valeur |
|----------|--------|
| **Repo** | gerivdb/BatMCP |
| **Local Path** | `D:\DO\WEB\TOOLS\L4-TOOLS\BatMCP` |
| **ADR** | ADR-2026-08-18-002-KIX-GENERIC-RUNNER-WRAPPER.md |
| **IntentHash** | 0xKIX_BATMCP_INTEGRATION_20260928 |

## 8. PREUVE-OF-LIFE

- [x] 2026-09-28T00:48:00+02:00 — Runner `batmcp` configuré dans `runners.yaml`
- [x] 2026-09-28T00:48:00+02:00 — GatewayRunner implémenté dans `runners/gateway_runner.py`
- [x] 2026-09-28T00:48:00+02:00 — Intégré dans PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER
- [x] 2026-09-28T00:48:00+02:00 — Capability model appliqué

## 9. RÉFÉRENCES

- `PRD-MOC-KIX-MASTER.md` : Master MOC KIX
- `PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER-2026-09-27.md` : Intégration écosystème master
- `config/runners.yaml` : Configuration runner
- `runners/gateway_runner.py` : Implémentation GatewayRunner

---

**IntentHash** : `0xKIX_BATMCP_INTEGRATION_20260928`
**Statut** : **implemented**
**Date** : 2026-09-28

*PRD-MOC-KIX-BATMCP — implemented — 2026-09-28*
