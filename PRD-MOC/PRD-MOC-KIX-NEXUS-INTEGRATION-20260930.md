---
type: PRD-MOC
version: "1.0"
date: "2026-09-30"
status: draft
intent_hash: 0xPRD_MOC_KIX_NEXUS_INTEGRATION_20260930
parent_prd: PRD-MOC/PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-20260926.md
pole_id: POLE-KG-TDC-001
owner: L2-PLATFORM
repo: gerivdb/KIX
related_adr: ADR-2026-05-14-004-KILO-CODE-HOTL-OPERATIONAL-STD
related_moc: PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-20260926.md, PRD-MOC-KIX-MASTER-20260926.md
---

# PRD-MOC - KIX × NEXUS Integration

## Résumé Exécutif

Intégration de KIX avec NEXUS (L0-CANON) pour accéder au méga-SOT (registre des registres) et respecter la gouvernance centralisée.

**Statut** : **draft** (2026-09-30)

---

## 1. Interface

### 1.1 Client NEXUS

**Fichier** : `src/nexus_registry_client.py`
**Protocole** : NEXUS registry protocol (REST/JSON)
**Health check** : `GET http://localhost:8801/health`
**Timeout** : 5s (configurable)

### 1.2 Méthodes

| Méthode | Paramètres | Retour | Description |
|---------|------------|--------|-------------|
| `get_registry(registry_name)` | registry_name: str | dict | Récupère un registre NEXUS |
| `list_repos()` | — | list | Liste tous les repos connus |
| `get_repo(repo_name)` | repo_name: str | dict | Récupère un repo par nom |
| `health()` | — | dict | Vérifie la santé du service |

---

## 2. Intégrations KIX

### 2.1 Accès au méga-SOT

```python
from nexus_registry_client import NexusRegistryClient

client = NexusRegistryClient()
repos = client.list_repos()
kix_repo = client.get_repo("gerivdb/KIX")
```

### 2.2 Validation de conformité

```python
registry = client.get_registry("known_repositories")
# Valider que KIX est conforme
```

---

## 3. Critères d'Acceptation

- [ ] `NexusRegistryClient` implémenté avec méthodes `get_registry`, `list_repos`, `get_repo`, `health`
- [ ] Tests unitaires pour chaque méthode (mock HTTP)
- [ ] Health check intégré dans `diagnostics.py::run_all_checks()`
- [ ] Respect BDCP : pas de `gh`, pas de GitHub Actions
- [ ] Timeout configurable (défaut 5s)
- [ ] Logging WAL des accès NEXUS

---

## 4. Proof-of-Life

- [ ] 2026-09-30T04:45:00+02:00 — Client NEXUS créé et testé

## 5. Références

- Parent : `PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-20260926.md`
- Master : `PRD-MOC-KIX-MASTER-20260926.md`
