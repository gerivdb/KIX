---
type: PRD-MOC
version: "1.0"
date: "2026-09-30"
status: draft
intent_hash: 0xPRD_MOC_KIX_TRIX_EXTENDED_20260930
parent_prd: PRD-MOC/PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-20260926.md
pole_id: POLE-KG-TDC-001
owner: L2-PLATFORM
repo: gerivdb/KIX
related_adr: ADR-2026-08-18-002-KIX-GENERIC-RUNNER-WRAPPER.md
related_moc: PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-20260926.md, PRD-MOC-KIX-MASTER-20260926.md
---

# PRD-MOC - KIX × TRIX Extended Integration

## Résumé Exécutif

Extension de l'intégration TRIX dans KIX pour couvrir l'ensemble des endpoints REST du Git Arbiter (kiva_run, kiva_stop, kiva_list, kiva_snapshot, kiva_restore).

**Statut** : **draft** (2026-09-30)

---

## 1. Interface

### 1.1 Client TRIX

**Fichier** : `src/trix_client.py`
**Protocole** : REST
**Endpoint** : `http://localhost:8742`
**Timeout** : 10s (configurable)

### 1.2 Méthodes

| Méthode | Endpoint | Paramètres | Retour | Statut |
|---------|----------|------------|--------|--------|
| `health()` | `GET /health` | — | dict | ✅ testé |
| `kiva_run(config)` | `POST /kiva-run` | config: dict | dict | ❌ non testé |
| `kiva_stop(container)` | `POST /containers/:name/stop` | container: str | dict | ❌ non testé |
| `kiva_list()` | `GET /kiva-list` | — | list | ❌ non testé |
| `kiva_snapshot(container)` | `POST /containers/:name/snapshot` | container: str | dict | ❌ non testé |
| `kiva_restore(container, snapshot)` | `POST /containers/:name/restore` | container: str, snapshot: str | dict | ❌ non testé |

---

## 2. Intégrations KIX

### 2.1 Gestion du cycle de vie

```python
from trix_client import TrixClient

client = TrixClient()
result = client.kiva_run({"image": "trixd", "cpu": 4})
client.kiva_stop("trixd-001")
containers = client.kiva_list()
```

---

## 3. Critères d'Acceptation

- [ ] `TrixClient` couvre tous les endpoints REST TRIX
- [ ] Tests unitaires pour chaque méthode (mock HTTP)
- [ ] Tests d'intégration contre TRIX réel (si disponible)
- [ ] Respect BDCP : pas de `gh`, pas de GitHub Actions
- [ ] Timeout configurable (défaut 10s)
- [ ] Logging WAL des opérations TRIX

---

## 4. Proof-of-Life

- [ ] 2026-09-30T04:55:00+02:00 — Client TRIX étendu créé et testé

## 5. Références

- Parent : `PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-20260926.md`
- Master : `PRD-MOC-KIX-MASTER-20260926.md`
