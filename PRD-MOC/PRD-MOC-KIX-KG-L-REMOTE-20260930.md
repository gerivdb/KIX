---
type: PRD-MOC
version: "1.0"
date: "2026-09-30"
status: draft
intent_hash: 0xPRD_MOC_KIX_KG_L_REMOTE_20260930
parent_prd: PRD-MOC/PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-20260926.md
pole_id: POLE-KG-TDC-001
owner: L2-PLATFORM
repo: gerivdb/KIX
related_adr: ADR-2026-08-18-002-KIX-GENERIC-RUNNER-WRAPPER.md
related_moc: PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-20260926.md, PRD-MOC-KIX-MASTER-20260926.md
---

# PRD-MOC - KIX × KG-L Remote HTTP Integration

## Résumé Exécutif

Implémentation du mode remote HTTP pour `KG_L_Client`, permettant à KIX d'interroger KG-L Engine via réseau (au lieu du mode local in-process uniquement).

**Statut** : **draft** (2026-09-30)

---

## 1. Interface

### 1.1 Client KG-L Remote

**Fichier** : `kix/libs/shared-clients/kg_l_client.py`
**Protocole** : HTTP/JSON
**Endpoint** : `http://localhost:8888`
**Timeout** : 10s (configurable)

### 1.2 Méthodes à implémenter

| Méthode | Endpoint HTTP | Paramètres | Retour |
|---------|---------------|------------|--------|
| `query(cypher, params)` | `POST /query` | cypher: str, params: dict | list[dict] |
| `get_hubs(limit, min_degree)` | `GET /hubs` | limit: int, min_degree: int | list |
| `get_graph_stats()` | `GET /stats` | — | dict |
| `ingest(anchors, edges)` | `POST /ingest` | anchors: list, edges: list | dict |
| `health()` | `GET /health` | — | dict |

---

## 2. Intégrations KIX

### 2.1 Mode remote

```python
from kg_l_client import KG_L_Client

# Mode remote (HTTP)
client = KG_L_Client(host="http://localhost:8888")
stats = client.get_graph_stats()
```

### 2.2 Fallback local → remote

```python
client = KG_L_Client(host="http://localhost:8888", data_path="kg_l/data")
# Si local échoue, fallback remote automatique
```

---

## 3. Critères d'Acceptation

- [ ] `KG_L_Client` supporte mode remote HTTP (actuellement stub)
- [ ] Tests unitaires pour chaque méthode HTTP (mock requests)
- [ ] Tests d'intégration contre KG-L Engine réel
- [ ] Health check intégré dans `diagnostics.py::run_all_checks()`
- [ ] Respect BDCP : pas de `gh`, pas de GitHub Actions
- [ ] Timeout configurable (défaut 10s)
- [ ] Logging WAL des requêtes Cypher

---

## 4. Proof-of-Life

- [ ] 2026-09-30T04:50:00+02:00 — Client KG-L remote créé et testé

## 5. Références

- Parent : `PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-20260926.md`
- Master : `PRD-MOC-KIX-MASTER-20260926.md`
