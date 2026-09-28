---
type: "PRD_MOC"
version: "1.0.0"
date: "2026-09-27"
updated: "2026-09-28"
status: "implemented"
intent_hash: "0xKIX_GATEWAY_MANAGER_INTEGRATION_20260927"
parent_doc: PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER-2026-09-27.md
related_adr: ADR-2026-08-20-001-bootstrap-runner.md, ADR-2026-08-18-002-KIX-GENERIC-RUNNER-WRAPPER.md
related_moc: PRD-MOC-KIX-MASTER.md, PRD-MOC-KIX-BOOTSTRAP-RUNNER-2026-08-20.md, PRD-MOC-VEX-KIX-BOUNDARIES-20260927.md
---

# PRD MOC - KIX - Integration GATEWAY-MANAGER

## 1. RÉSUMÉ EXÉCUTIF

Ce PRD MOC couvre l'integration de **GATEWAY-MANAGER** (gerivdb/GATEWAY-MANAGER) dans KIX comme runner de type `gateway-exe`.

**Role** : Proxy/reverse proxy, BDCP, Clapet, PAT rotation
**Port** : 9000 (legacy), 18000 (ECOS-CLI)
**Type** : gateway-exe
**Strate** : L1-INFRA
**Statut** : ✅ **Integre**

## 2. CONFIGURATION RUNNER

```yaml
- name: gateway-manager
  runner_type: gateway-exe
  port: 9000
  working_dir: D:/DO/WEB/TOOLS/L1-INFRA/GATEWAY-MANAGER
  binary: gateway-manager.exe
  depends_on: [kix]
  restart_policy: always
```

## 3. RESPONSABILITÉS

| Domaine | Responsable | Description |
|---------|-------------|-------------|
| BDCP proxy | ✅ GATEWAY-MANAGER | Proxy derriere CDP, anonymat reseau |
| Clapet | ✅ GATEWAY-MANAGER | `POST /clapet/open|close` |
| PAT rotation | ✅ GATEWAY-MANAGER | Rotation automatique des tokens GitHub |
| SecretResolver | ✅ bootstrap | Resolution de secrets (delegue au bootstrap) |

## 4. POINTS D'INTÉGRATION KIX

| Point | Protocole | Description |
|-------|-----------|-------------|
| KIX -> GATEWAY-MANAGER | REST + WAZAA | Health checks, orchestration |
| bootstrap -> GATEWAY-MANAGER | TCP/HTTP | Verification dependance critique |
| VEX -> GATEWAY-MANAGER | REST | Health check cross-layer |

## 5. ENDPOINTS UTILISÉS PAR KIX

| Endpoint | Methode | Usage KIX |
|----------|---------|-----------|
| `/health` | GET | Health check |
| `/clapet/status` | GET | Verification etat BDCP |
| `/clapet/open` | POST | Sortie BDCP (admin only) |
| `/clapet/close` | POST | Retour BDCP |

## 6. GOUVERNANCE

| Attribut | Valeur |
|----------|--------|
| **Repo** | gerivdb/GATEWAY-MANAGER |
| **Local Path** | `D:\DO\WEB\TOOLS\L1-INFRA\GATEWAY-MANAGER` |
| **ADR** | ADR-2026-08-20-001-bootstrap-runner.md |
| **IntentHash** | 0xKIX_GATEWAY_MANAGER_INTEGRATION_20260927 |

## 7. PREUVE-OF-LIFE

- [x] 2026-09-27T23:00:00+02:00 -- Runner `gateway-manager` configure dans `runners.yaml`
- [x] 2026-09-27T23:00:00+02:00 -- working_dir et binary definis
- [x] 2026-09-27T23:00:00+02:00 -- Integre dans PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER
- [x] 2026-09-27T23:00:00+02:00 -- Capability model documente

## 8. RÉFÉRENCES

- `PRD-MOC-KIX-MASTER.md` : Master MOC KIX
- `PRD-MOC-KIX-BOOTSTRAP-RUNNER-2026-08-20.md` : Bootstrap runner
- `PRD-MOC-VEX-KIX-BOUNDARIES-20260927.md` : Frontieres KIX/VEX
- `config/runners.yaml` : Configuration runner
- `runners/gateway_runner.py` : Implementation GatewayRunner

---

**IntentHash** : `0xKIX_GATEWAY_MANAGER_INTEGRATION_20260927`
**Statut** : **implemented**
**Date** : 2026-09-27

*PRD-MOC-KIX-GATEWAY-MANAGER -- implemented -- 2026-09-27*
