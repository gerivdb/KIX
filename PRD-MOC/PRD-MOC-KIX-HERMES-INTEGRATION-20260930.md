---
type: PRD-MOC
version: "1.0"
date: "2026-09-30"
status: draft
intent_hash: 0xPRD_MOC_KIX_HERMES_INTEGRATION_20260930
parent_prd: PRD-MOC/PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-20260926.md
pole_id: POLE-KG-TDC-001
owner: L2-PLATFORM
repo: gerivdb/KIX
related_adr: ADR-2026-08-18-002-KIX-GENERIC-RUNNER-WRAPPER.md
related_moc: PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-20260926.md, PRD-MOC-KIX-MASTER-20260926.md
---

# PRD-MOC - KIX × HERMES Integration

## Résumé Exécutif

Intégration de KIX avec HERMES/Mnemo (L1-INFRA) pour lire/écrire dans Mnemo via WAZAA bus et recevoir des skills recommandés.

**Statut** : **draft** (2026-09-30)

---

## 1. Interface

### 1.1 Client HERMES

**Fichier** : `src/hermes_memory_client.py`
**Protocole** : REST + WAZAA bus
**Health check** : `GET /health/hermes`
**Timeout** : 5s (configurable)

### 1.2 Méthodes

| Méthode | Paramètres | Retour | Description |
|---------|------------|--------|-------------|
| `read_memory(key)` | key: str | dict | Lit une entrée Mnemo |
| `write_memory(key, value)` | key: str, value: dict | bool | Écrit dans Mnemo |
| `get_recommended_skills()` | — | list | Récupère les skills recommandés |
| `publish_fact(fact)` | fact: dict | bool | Publie un fait vérifié |
| `health()` | — | dict | Vérifie la santé du service |

---

## 2. Intégrations KIX

### 2.1 Lecture/Écriture Mnemo

```python
from hermes_memory_client import HermesMemoryClient

client = HermesMemoryClient()
client.write_memory("runner:trixd:status", {"status": "running", "pid": 1234})
data = client.read_memory("runner:trixd:status")
```

### 2.2 Skills recommandés

```python
skills = client.get_recommended_skills()
for skill in skills:
    # Installer/utiliser le skill
    pass
```

---

## 3. Critères d'Acceptation

- [ ] `HermesMemoryClient` implémenté avec méthodes `read_memory`, `write_memory`, `get_recommended_skills`, `publish_fact`, `health`
- [ ] Tests unitaires pour chaque méthode (mock HTTP + WAZAA)
- [ ] Health check intégré dans `diagnostics.py::run_all_checks()`
- [ ] Respect BDCP : pas de `gh`, pas de GitHub Actions
- [ ] Timeout configurable (défaut 5s)
- [ ] Logging WAL des accès Mnemo

---

## 4. Proof-of-Life

- [ ] 2026-09-30T04:40:00+02:00 — Client HERMES créé et testé

## 5. Références

- Parent : `PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-20260926.md`
- Master : `PRD-MOC-KIX-MASTER-20260926.md`
