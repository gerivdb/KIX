---
type: "PRD_MOC"
version: "1.0.0"
date: "2026-09-28"
updated: "2026-09-28"
status: "implemented"
intent_hash: "0xKIX_TLM_LANG_INTEGRATION_20260928"
parent_doc: PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER-2026-09-27.md
related_adr: ADR-2026-08-18-002-KIX-GENERIC-RUNNER-WRAPPER.md, ADR-2026-07-28-001-tlm-lang-runner
related_moc: PRD-MOC-KIX-MASTER.md, PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER-2026-09-27.md
---

# PRD MOC - KIX - Intégration TLM-LANG

## 1. RÉSUMÉ EXÉCUTIF

Ce PRD MOC couvre l'intégration de **TLM-LANG** dans KIX comme runner de type `python`.

**Rôle** : TLM (Ternary Logic Machine)
**Port** : 8803
**Type** : python
**Strate** : L0-CANON
**Statut** : ✅ **Intégré**

## 2. CONFIGURATION RUNNER

```yaml
- name: tlm-lang
  runner_type: python
  port: 8803
  working_dir: D:\DO\WEB\TOOLS\L0-CANON\unified-design\designs\tlm-lang
  entrypoint: runners/tlm_lang_fastapi.py
  depends_on: [kix]
  health_path: /health
  restart_policy: on-failure
  meta:
    repo: gerivdb/tlm-lang
    role: cognitive
```

## 3. RESPONSABILITÉS

| Domaine | Responsable | Description |
|---------|-------------|-------------|
| Logique ternaire | ✅ TLM-LANG | Moteur TLM |
| Inférence | ✅ TLM-LANG | Inférence TLM |

## 4. POINTS D'INTÉGRATION KIX

| Point | Protocole | Description |
|-------|-----------|-------------|
| KIX → TLM-LANG | REST | Health checks, orchestration |
| bootstrap → TLM-LANG | HTTP | Vérification dépendance |

## 5. ENDPOINTS UTILISÉS PAR KIX

| Endpoint | Méthode | Usage KIX |
|----------|---------|-----------|
| `/health` | GET | Health check |

## 6. CAPABILITY MODEL

| Runner | meta.role | Capabilities |
|--------|-----------|--------------|
| tlm-lang | `cognitive` | `runner:start`, `runner:stop`, `health:check` |

## 7. GOUVERNANCE

| Attribut | Valeur |
|----------|--------|
| **Repo** | gerivdb/tlm-lang |
| **Local Path** | `D:\DO\WEB\TOOLS\L0-CANON\unified-design\designs\tlm-lang` |
| **ADR** | ADR-2026-08-18-002-KIX-GENERIC-RUNNER-WRAPPER.md, ADR-2026-07-28-001-tlm-lang-runner |
| **IntentHash** | 0xKIX_TLM_LANG_INTEGRATION_20260928 |

## 8. PREUVE-OF-LIFE

- [x] 2026-09-28T02:45:00+02:00 — Runner `tlm-lang` configuré dans `runners.yaml`
- [x] 2026-09-28T02:45:00+02:00 — PythonRunner implémenté dans `runners/python_runner.py`
- [x] 2026-09-28T02:45:00+02:00 — Intégré dans PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER

## 9. RÉFÉRENCES

- `PRD-MOC-KIX-MASTER.md` : Master MOC KIX
- `PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER-2026-09-27.md` : Intégration écosystème master
- `config/runners.yaml` : Configuration runner
- `runners/python_runner.py` : Implémentation PythonRunner

---

**IntentHash** : `0xKIX_TLM_LANG_INTEGRATION_20260928`
**Statut** : **implemented**
**Date** : 2026-09-28

*PRD-MOC-KIX-TLM-LANG — implemented — 2026-09-28*
