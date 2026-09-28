---
type: "PRD_MOC"
version: "1.0.0"
date: "2026-09-28"
updated: "2026-09-28"
status: "implemented"
intent_hash: "0xKIX_ECOS_CLI_INTEGRATION_20260928"
parent_doc: PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER-2026-09-27.md
related_adr: ADR-2026-08-18-002-KIX-GENERIC-RUNNER-WRAPPER.md, ADR-2026-08-20-001-bootstrap-runner.md
related_moc: PRD-MOC-KIX-MASTER.md, PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER-2026-09-27.md, PRD-MOC-KIX-BOOTSTRAP-RUNNER-2026-08-20.md
---

# PRD MOC - KIX - Intégration ECOS-CLI

## 1. RÉSUMÉ EXÉCUTIF

Ce PRD MOC couvre l'intégration de **ECOS-CLI** (gerivdb/ECOS-CLI) dans KIX comme runner de type `gateway-exe`.

**Rôle** : Point d'entrée opérationnel, LLM gateway, BDCP
**Port** : 18000
**Type** : gateway-exe
**Strate** : L1-INFRA
**Statut** : ✅ **Intégré**

## 2. CONFIGURATION RUNNER

```yaml
- name: llm-gateway
  runner_type: gateway-exe
  port: 18000
  working_dir: D:/DO/WEB/TOOLS/L1-INFRA/ECOS-CLI
  depends_on: [kix]
  health_path: /health
  restart_policy: on-failure
  log_file: D:/DO/WEB/TOOLS/L1-INFRA/ECOS-CLI/logs/llm-gateway.log
  pid_file: D:/DO/WEB/TOOLS/L1-INFRA/ECOS-CLI/logs/llm-gateway.pid
  meta:
    repo: gerivdb/ECOS-CLI
    role: llm-gateway
  binary: gateway-manager.exe
```

## 3. RESPONSABILITÉS

| Domaine | Responsable | Description |
|---------|-------------|-------------|
| LLM Gateway | ✅ ECOS-CLI | Point d'entrée opérationnel pour LLM |
| BDCP | ✅ ECOS-CLI | Gestion du clapet BDCP |
| PAT rotation | ✅ ECOS-CLI | Rotation des tokens GitHub |
| Bootstrap | ✅ ECOS-CLI | Intégration avec bootstrap runner |

## 4. POINTS D'INTÉGRATION KIX

| Point | Protocole | Description |
|-------|-----------|-------------|
| KIX → ECOS-CLI | REST + WAZAA | Health checks, orchestration |
| bootstrap → ECOS-CLI | TCP/HTTP | Vérification dépendance critique |

## 5. ENDPOINTS UTILISÉS PAR KIX

| Endpoint | Méthode | Usage KIX |
|----------|---------|-----------|
| `/health` | GET | Health check |
| `/clapet/status` | GET | Vérification état BDCP |

## 6. CAPABILITY MODEL

| Runner | meta.role | Capabilities |
|--------|-----------|--------------|
| llm-gateway | `llm-gateway` | `runner:start`, `runner:stop`, `health:check` |

## 7. GOUVERNANCE

| Attribut | Valeur |
|----------|--------|
| **Repo** | gerivdb/ECOS-CLI |
| **Local Path** | `D:\DO\WEB\TOOLS\L1-INFRA\ECOS-CLI` |
| **ADR** | ADR-2026-08-18-002-KIX-GENERIC-RUNNER-WRAPPER.md, ADR-2026-08-20-001-bootstrap-runner.md |
| **IntentHash** | 0xKIX_ECOS_CLI_INTEGRATION_20260928 |

## 8. PREUVE-OF-LIFE

- [x] 2026-09-28T00:48:00+02:00 — Runner `llm-gateway` configuré dans `runners.yaml`
- [x] 2026-09-28T00:48:00+02:00 — GatewayRunner implémenté dans `runners/gateway_runner.py`
- [x] 2026-09-28T00:48:00+02:00 — Intégré dans PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER
- [x] 2026-09-28T00:48:00+02:00 — Capability model appliqué

## 9. RÉFÉRENCES

- `PRD-MOC-KIX-MASTER.md` : Master MOC KIX
- `PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER-2026-09-27.md` : Intégration écosystème master
- `PRD-MOC-KIX-BOOTSTRAP-RUNNER-2026-08-20.md` : Bootstrap runner
- `config/runners.yaml` : Configuration runner
- `runners/gateway_runner.py` : Implémentation GatewayRunner

---

**IntentHash** : `0xKIX_ECOS_CLI_INTEGRATION_20260928`
**Statut** : **implemented**
**Date** : 2026-09-28

*PRD-MOC-KIX-ECOS-CLI — implemented — 2026-09-28*
