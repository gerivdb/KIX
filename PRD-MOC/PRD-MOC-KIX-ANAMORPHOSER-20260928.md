---
type: "PRD_MOC"
version: "1.0.0"
date: "2026-09-28"
updated: "2026-09-28"
status: "implemented"
intent_hash: "0xKIX_ANAMORPHOSER_INTEGRATION_20260928"
parent_doc: PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER-2026-09-27.md
related_adr: ADR-2026-08-18-002-KIX-GENERIC-RUNNER-WRAPPER.md
related_moc: PRD-MOC-KIX-MASTER.md, PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER-2026-09-27.md
---

# PRD MOC - KIX - Integration Anamorphoser

## 1. RÉSUMÉ EXÉCUTIF

Ce PRD MOC couvre l'integration de **Anamorphoser** dans KIX comme runner de type `python`.

**Role** : Gouvernance, metamorphose
**Port** : 8831
**Type** : python
**Strate** : L0-CANON
**Statut** : ✅ **Integre**

## 2. CONFIGURATION RUNNER

```yaml
- name: anamorphoser
  runner_type: python
  port: 8831
  working_dir: D:\DO\WEB\TOOLS\L0-CANON\GOVERNANCE-HUB
  entrypoint: runners/anamorphoser_fastapi.py
  depends_on: [kix]
  health_path: /health
  restart_policy: on-failure
  meta:
    repo: gerivdb/anamorphoser
    role: cognitive
```

## 3. RESPONSABILITÉS

| Domaine | Responsable | Description |
|---------|-------------|-------------|
| Metamorphose | ✅ Anamorphoser | Transformation de modeles |
| Gouvernance | ✅ Anamorphoser | Processus de gouvernance |

## 4. POINTS D'INTÉGRATION KIX

| Point | Protocole | Description |
|-------|-----------|-------------|
| KIX -> Anamorphoser | REST | Health checks, orchestration |
| bootstrap -> Anamorphoser | HTTP | Verification dependance |

## 5. ENDPOINTS UTILISÉS PAR KIX

| Endpoint | Methode | Usage KIX |
|----------|---------|-----------|
| `/health` | GET | Health check |

## 6. CAPABILITY MODEL

| Runner | meta.role | Capabilities |
|--------|-----------|--------------|
| anamorphoser | `cognitive` | `runner:start`, `runner:stop`, `health:check` |

## 7. GOUVERNANCE

| Attribut | Valeur |
|----------|--------|
| **Repo** | gerivdb/anamorphoser |
| **Local Path** | `D:\DO\WEB\TOOLS\L0-CANON\GOVERNANCE-HUB` |
| **ADR** | ADR-2026-08-18-002-KIX-GENERIC-RUNNER-WRAPPER.md |
| **IntentHash** | 0xKIX_ANAMORPHOSER_INTEGRATION_20260928 |

## 8. PREUVE-OF-LIFE

- [x] 2026-09-28T02:45:00+02:00 -- Runner `anamorphoser` configure dans `runners.yaml`
- [x] 2026-09-28T02:45:00+02:00 -- PythonRunner implemente dans `runners/python_runner.py`
- [x] 2026-09-28T02:45:00+02:00 -- Integre dans PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER

## 9. RÉFÉRENCES

- `PRD-MOC-KIX-MASTER.md` : Master MOC KIX
- `PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER-2026-09-27.md` : Integration ecosysteme master
- `config/runners.yaml` : Configuration runner
- `runners/python_runner.py` : Implementation PythonRunner

---

**IntentHash** : `0xKIX_ANAMORPHOSER_INTEGRATION_20260928`
**Statut** : **implemented**
**Date** : 2026-09-28

*PRD-MOC-KIX-ANAMORPHOSER -- implemented -- 2026-09-28*
