---
type: "PRD_MOC"
version: "1.0.0"
date: "2026-09-27"
updated: "2026-09-28"
status: "implemented"
intent_hash: "0xKIX_FLEX_INTEGRATION_20260927"
parent_doc: PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER-2026-09-27.md
related_adr: ADR-2026-08-18-002-KIX-GENERIC-RUNNER-WRAPPER.md, ADR-2026-09-24-KIX-MULTI-LANG-RUNNERS.md
related_moc: PRD-MOC-KIX-MASTER.md, PRD-MOC-KIX-MULTI-LANG-ECOSYSTEM-2026-09-24.md
---

# PRD MOC - KIX - Integration FLEX

## 1. RÉSUMÉ EXÉCUTIF

Ce PRD MOC couvre l'integration de **FLEX** (gerivdb/FLEX) dans KIX comme runner de type `python` et `rust`.

**Role** : Cache/Flex, API REST
**Port** : 8080 (flex-api), 7718 (flex-rust), 7719 (flex-api KIX)
**Type** : python / rust
**Strate** : L4-TOOLS
**Statut** : ✅ **Integre**

## 2. CONFIGURATION RUNNER

```yaml
- name: flex-api
  runner_type: python
  port: 7719
  working_dir: D:/DO/WEB/TOOLS/L4-TOOLS/FLEX
  entrypoint: flex_api.py
  depends_on: [kix]
  restart_policy: always

- name: flex-rust
  runner_type: rust
  port: 7718
  working_dir: D:/DO/WEB/TOOLS/L4-TOOLS/FLEX
  binary: flex-rust.exe
  depends_on: [kix]
  restart_policy: always
```

## 3. RESPONSABILITÉS

| Domaine | Responsable | Description |
|---------|-------------|-------------|
| Cache | ✅ FLEX | Cache distribue |
| API REST | ✅ FLEX | Endpoints REST FLEX |
| Rust service | ✅ FLEX | Service Rust haute performance |

## 4. POINTS D'INTÉGRATION KIX

| Point | Protocole | Description |
|-------|-----------|-------------|
| KIX -> FLEX | REST + WAZAA | Health checks, orchestration |
| bootstrap -> FLEX | HTTP | Verification dependance optionnelle |

## 5. ENDPOINTS UTILISÉS PAR KIX

| Endpoint | Methode | Usage KIX |
|----------|---------|-----------|
| `/health` | GET | Health check |
| `/api/status` | GET | Status du service |

## 6. CAPABILITY MODEL

| Runner | meta.role | Capabilities |
|--------|-----------|--------------|
| flex-api | `api` | `runner:start`, `runner:stop`, `health:check` |
| flex-rust | `rust-service` | `runner:start`, `runner:stop`, `health:check` |

## 7. GOUVERNANCE

| Attribut | Valeur |
|----------|--------|
| **Repo** | gerivdb/FLEX |
| **Local Path** | `D:\DO\WEB\TOOLS\L4-TOOLS\FLEX` |
| **ADR** | ADR-2026-09-24-KIX-MULTI-LANG-RUNNERS.md |
| **IntentHash** | 0xKIX_FLEX_INTEGRATION_20260927 |

## 8. PREUVE-OF-LIFE

- [x] 2026-09-27T23:00:00+02:00 -- Runners `flex-api` et `flex-rust` configures dans `runners.yaml`
- [x] 2026-09-27T23:00:00+02:00 -- PythonRunner et RustRunner implementes
- [x] 2026-09-27T23:00:00+02:00 -- Integre dans PRD-MOC-KIX-MULTI-LANG-ECOSYSTEM
- [x] 2026-09-27T23:00:00+02:00 -- Capability model applique

## 9. RÉFÉRENCES

- `PRD-MOC-KIX-MASTER.md` : Master MOC KIX
- `PRD-MOC-KIX-MULTI-LANG-ECOSYSTEM-2026-09-24.md` : Multi-lang ecosystem
- `config/runners.yaml` : Configuration runner
- `runners/python_runner.py` : Implementation PythonRunner
- `runners/rust_runner.py` : Implementation RustRunner

---

**IntentHash** : `0xKIX_FLEX_INTEGRATION_20260927`
**Statut** : **implemented**
**Date** : 2026-09-27

*PRD-MOC-KIX-FLEX -- implemented -- 2026-09-27*
