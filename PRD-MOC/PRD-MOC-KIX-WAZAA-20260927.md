---
type: "PRD_MOC"
version: "1.0.0"
date: "2026-09-27"
updated: "2026-09-28"
status: "implemented"
intent_hash: "0xKIX_WAZAA_INTEGRATION_20260927"
parent_doc: PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER-2026-09-27.md
related_adr: ADR-2026-08-18-002-KIX-GENERIC-RUNNER-WRAPPER.md
related_moc: PRD-MOC-KIX-MASTER.md, PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER-2026-09-27.md
---

# PRD MOC - KIX - Intégration WAZAA

## 1. RÉSUMÉ EXÉCUTIF

Ce PRD MOC couvre l'intégration de **WAZAA** (gerivdb/WAZAA) dans KIX comme runner de type `python`.

**Rôle** : Bus événementiel, WAZAA bus, coordination
**Port** : 1873 (wazaa), 5002 (wazaa-bus)
**Type** : python
**Strate** : L4-TOOLS
**Statut** : ✅ **Intégré**

## 2. CONFIGURATION RUNNER

```yaml
- name: wazaa
  runner_type: python
  port: 1873
  working_dir: D:/DO/WEB/TOOLS/L4-TOOLS/WAZAA
  entrypoint: -m wazaa.wazaa_server
  depends_on: [kix]
  restart_policy: always

- name: wazaa-bus
  runner_type: python
  port: 5002
  working_dir: D:/DO/WEB/TOOLS/L4-TOOLS/WAZAA
  entrypoint: wazaa_bus.py
  depends_on: [kix]
  restart_policy: always
```

## 3. RESPONSABILITÉS

| Domaine | Responsable | Description |
|---------|-------------|-------------|
| Bus événementiel | ✅ WAZAA | Publication/consommation d'événements |
| Coordination L3 | ✅ WAZAA | Coordination avec VEX (L3) |
| Swarm status | ✅ WAZAA | État agrégé pour Agent Manager |
| Alertes | ✅ WAZAA | Publication d'alertes critiques |

## 4. POINTS D'INTÉGRATION KIX

| Point | Protocole | Description |
|-------|-----------|-------------|
| KIX → WAZAA | WAZAA Bus TCP (1873) | Publication événements |
| bootstrap → WAZAA | WAZAA Bus TCP (1873) | Événements bootstrap |
| Agent Manager → WAZAA | WAZAA Bus TCP (1873) | Swarm status |
| VEX → WAZAA | WAZAA Bus TCP (1873) | Coordination L3 |

## 5. ENDPOINTS UTILISÉS PAR KIX

| Endpoint | Méthode | Usage KIX |
|----------|---------|-----------|
| `/health` | GET | Health check |
| `/publish` | POST | Publication d'événements |
| `/subscribe` | POST | Abonnement à des topics |

## 6. CAPABILITY MODEL

| Runner | meta.role | Capabilities |
|--------|-----------|--------------|
| wazaa | `dashboard` | `runner:start`, `runner:stop`, `health:check` |
| wazaa-bus | `event-bus` | `runner:start`, `runner:stop`, `health:check` |

## 7. GOUVERNANCE

| Attribut | Valeur |
|----------|--------|
| **Repo** | gerivdb/WAZAA |
| **Local Path** | `D:\DO\WEB\TOOLS\L4-TOOLS\WAZAA` |
| **ADR** | ADR-2026-08-18-002-KIX-GENERIC-RUNNER-WRAPPER.md |
| **IntentHash** | 0xKIX_WAZAA_INTEGRATION_20260927 |

## 8. PREUVE-OF-LIFE

- [x] 2026-09-27T23:00:00+02:00 — Runner `wazaa` configuré dans `runners.yaml`
- [x] 2026-09-27T23:00:00+02:00 — PythonRunner implémenté dans `runners/python_runner.py`
- [x] 2026-09-27T23:00:00+02:00 — Intégré dans PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER
- [x] 2026-09-27T23:00:00+02:00 — WAZAA bus connectivity validée

## 9. RÉFÉRENCES

- `PRD-MOC-KIX-MASTER.md` : Master MOC KIX
- `PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER-2026-09-27.md` : Intégration écosystème master
- `config/runners.yaml` : Configuration runner
- `runners/python_runner.py` : Implémentation PythonRunner
- `src/kix_bridge_wazaa.py` : Bridge KIX-WAZAA

---

**IntentHash** : `0xKIX_WAZAA_INTEGRATION_20260927`
**Statut** : **implemented**
**Date** : 2026-09-27

*PRD-MOC-KIX-WAZAA — implemented — 2026-09-27*
