---
type: "PRD_MOC"
version: "1.0.0"
date: "2026-09-27"
updated: "2026-09-28"
status: "implemented"
intent_hash: "0xKIX_VEX_INTEGRATION_20260927"
parent_doc: PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER-2026-09-27.md
related_adr: ADR-2026-08-18-002-KIX-GENERIC-RUNNER-WRAPPER.md, ADR-2026-09-24-ECOSYSTEM-INTEGRATION.md
related_moc: PRD-MOC-KIX-MASTER.md, PRD-MOC-VEX-KIX-BOUNDARIES-20260927.md
---

# PRD MOC - KIX - Integration VEX

## 1. RÉSUMÉ EXÉCUTIF

Ce PRD MOC couvre l'integration de **VEX** (gerivdb/VEX) dans KIX comme partenaire L3.

**Role** : L3-ORCHESTRATOR -- Orchestrateur L3 des daemons/agents autonomes
**Port** : N/A (L3 orchestrateur)
**Type** : L3-CITIZENS
**Strate** : L3-CITIZENS
**Statut** : ✅ **Documente**

## 2. RESPONSABILITÉS

| Domaine | Responsable | Description |
|---------|-------------|-------------|
| Daemons L3 | ✅ VEX | Orchestration des daemons/agents autonomes |
| Deploiement multi-OS | ✅ VEX | NSSM/schtasks/systemd |
| Clients d'integration | ✅ VEX | Clients cross-platform |

## 3. FRONTIÈRES KIX/VEX

Voir `PRD-MOC-VEX-KIX-BOUNDARIES-20260927.md` pour le contrat complet de frontieres.

| Point | KIX (L2) | VEX (L3) |
|-------|----------|----------|
| Runners RLM | ✅ Responsable | ❌ |
| Daemons L3 | ❌ | ✅ Responsable |
| Health checks | `/health/kix` | `/health` agrege L3 |
| WAZAA bus | ✅ Utilise | ✅ Utilise |
| Bootstrap | ✅ Responsable | ❌ |

## 4. POINTS D'INTÉGRATION

| Point | Protocole | Description |
|-------|-----------|-------------|
| KIX -> VEX | REST | `GET /health/kix` |
| VEX -> KIX | REST | `GET /health`, `POST /health/l3` |
| KIX ↔ VEX | WAZAA Bus | Évenements daemons et runners |

## 5. CAPABILITY MODEL

VEX consulte KIX en tant que `viewer` sur les endpoints :
- `GET /health/kix` -- `health:read`
- `GET /swarm/status` -- `swarm:read`

## 6. GOUVERNANCE

| Attribut | Valeur |
|----------|--------|
| **Repo** | gerivdb/VEX |
| **Local Path** | `D:\DO\WEB\TOOLS\L3-CITIZENS\VEX` |
| **Statut** | active |
| **IntentHash** | 0xKIX_VEX_INTEGRATION_20260927 |

## 7. PREUVE-OF-LIFE

- [x] 2026-09-27T23:00:00+02:00 -- VEX reference dans PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER
- [x] 2026-09-27T23:00:00+02:00 -- PRD-MOC-VEX-KIX-BOUNDARIES cree et implemente
- [x] 2026-09-27T23:00:00+02:00 -- Endpoints `/health/kix`, `/health/l3` implementes
- [x] 2026-09-27T23:00:00+02:00 -- Capability model documente pour frontieres

## 8. RÉFÉRENCES

- `PRD-MOC-KIX-MASTER.md` : Master MOC KIX
- `PRD-MOC-VEX-KIX-BOUNDARIES-20260927.md` : Contrat de frontieres KIX/VEX
- `PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER-2026-09-27.md` : Integration ecosysteme master
- `src/app.py` : Endpoints `/health/kix`, `/health/l3`

---

**IntentHash** : `0xKIX_VEX_INTEGRATION_20260927`
**Statut** : **implemented**
**Date** : 2026-09-27

*PRD-MOC-KIX-VEX -- implemented -- 2026-09-27*
