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

# PRD MOC - KIX - Intégration VEX

## 1. RÉSUMÉ EXÉCUTIF

Ce PRD MOC couvre l'intégration de **VEX** (gerivdb/VEX) dans KIX comme partenaire L3.

**Rôle** : L3-ORCHESTRATOR — Orchestrateur L3 des daemons/agents autonomes
**Port** : N/A (L3 orchestrateur)
**Type** : L3-CITIZENS
**Strate** : L3-CITIZENS
**Statut** : ✅ **Documenté**

## 2. RESPONSABILITÉS

| Domaine | Responsable | Description |
|---------|-------------|-------------|
| Daemons L3 | ✅ VEX | Orchestration des daemons/agents autonomes |
| Déploiement multi-OS | ✅ VEX | NSSM/schtasks/systemd |
| Clients d'intégration | ✅ VEX | Clients cross-platform |

## 3. FRONTIÈRES KIX/VEX

Voir `PRD-MOC-VEX-KIX-BOUNDARIES-20260927.md` pour le contrat complet de frontières.

| Point | KIX (L2) | VEX (L3) |
|-------|----------|----------|
| Runners RLM | ✅ Responsable | ❌ |
| Daemons L3 | ❌ | ✅ Responsable |
| Health checks | `/health/kix` | `/health` agrégé L3 |
| WAZAA bus | ✅ Utilise | ✅ Utilise |
| Bootstrap | ✅ Responsable | ❌ |

## 4. POINTS D'INTÉGRATION

| Point | Protocole | Description |
|-------|-----------|-------------|
| KIX → VEX | REST | `GET /health/kix` |
| VEX → KIX | REST | `GET /health`, `POST /health/l3` |
| KIX ↔ VEX | WAZAA Bus | Événements daemons et runners |

## 5. CAPABILITY MODEL

VEX consulte KIX en tant que `viewer` sur les endpoints :
- `GET /health/kix` — `health:read`
- `GET /swarm/status` — `swarm:read`

## 6. GOUVERNANCE

| Attribut | Valeur |
|----------|--------|
| **Repo** | gerivdb/VEX |
| **Local Path** | `D:\DO\WEB\TOOLS\L3-CITIZENS\VEX` |
| **Statut** | active |
| **IntentHash** | 0xKIX_VEX_INTEGRATION_20260927 |

## 7. PREUVE-OF-LIFE

- [x] 2026-09-27T23:00:00+02:00 — VEX référencé dans PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER
- [x] 2026-09-27T23:00:00+02:00 — PRD-MOC-VEX-KIX-BOUNDARIES créé et implémenté
- [x] 2026-09-27T23:00:00+02:00 — Endpoints `/health/kix`, `/health/l3` implémentés
- [x] 2026-09-27T23:00:00+02:00 — Capability model documenté pour frontières

## 8. RÉFÉRENCES

- `PRD-MOC-KIX-MASTER.md` : Master MOC KIX
- `PRD-MOC-VEX-KIX-BOUNDARIES-20260927.md` : Contrat de frontières KIX/VEX
- `PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER-2026-09-27.md` : Intégration écosystème master
- `src/app.py` : Endpoints `/health/kix`, `/health/l3`

---

**IntentHash** : `0xKIX_VEX_INTEGRATION_20260927`
**Statut** : **implemented**
**Date** : 2026-09-27

*PRD-MOC-KIX-VEX — implemented — 2026-09-27*
