---
type: PRD-MOC
version: "1.0"
date: "2026-09-30"
status: draft
intent_hash: 0xPRD_MOC_KIX_BRAIN_INTEGRATION_20260930
parent_prd: PRD-MOC/PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-20260926.md
pole_id: POLE-KG-TDC-001
owner: L2-PLATFORM
repo: gerivdb/KIX
related_adr: ADR-2026-08-18-002-KIX-GENERIC-RUNNER-WRAPPER.md
related_moc: PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-20260926.md, PRD-MOC-KIX-MASTER-20260926.md
---

# PRD-MOC - KIX × BRAIN Integration

## Résumé Exécutif

Intégration de KIX avec BRAIN (L0-CANON) pour déclencher des agents cognitifs et recevoir des résultats via JSON-RPC 2.0 over HTTP.

**Statut** : **draft** (2026-09-30)

---

## 1. Interface

### 1.1 Client BRAIN

**Fichier** : `src/brain_cognitive_client.py`
**Protocole** : JSON-RPC 2.0 over HTTP
**Health check** : `GET http://localhost:8800/health`
**Timeout** : 5s (configurable)

### 1.2 Méthodes

| Méthode | Paramètres | Retour | Description |
|---------|------------|--------|-------------|
| `trigger_agent(agent_name, context)` | agent_name: str, context: dict | dict | Déclenche un agent cognitif BRAIN |
| `get_result(task_id)` | task_id: str | dict | Récupère le résultat d'une tâche BRAIN |
| `health()` | — | dict | Vérifie la santé du service BRAIN |

---

## 2. Intégrations KIX

### 2.1 Déclenchement d'agents

```python
from brain_cognitive_client import BrainCognitiveClient

client = BrainCognitiveClient()
result = client.trigger_agent("architect", {"epic": "EPIC-123"})
```

### 2.2 Réception de résultats

```python
result = client.get_result(task_id)
if result["status"] == "completed":
    # Traiter le résultat
    pass
```

---

## 3. Critères d'Acceptation

- [ ] `BrainCognitiveClient` implémenté avec méthodes `trigger_agent`, `get_result`, `health`
- [ ] Tests unitaires pour chaque méthode (mock HTTP)
- [ ] Health check intégré dans `diagnostics.py::check_runners()`
- [ ] Respect BDCP : pas de `gh`, pas de GitHub Actions
- [ ] Timeout configurable (défaut 5s)
- [ ] Logging WAL des événements BRAIN

---

## 4. Proof-of-Life

- [ ] 2026-09-30T04:30:00+02:00 — Client BRAIN créé et testé

## 5. Références

- Parent : `PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-20260926.md`
- Master : `PRD-MOC-KIX-MASTER-20260926.md`
