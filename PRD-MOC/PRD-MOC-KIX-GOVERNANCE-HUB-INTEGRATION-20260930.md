---
type: PRD-MOC
version: "1.0"
date: "2026-09-30"
status: draft
intent_hash: 0xPRD_MOC_KIX_GOVERNANCE_HUB_INTEGRATION_20260930
parent_prd: PRD-MOC/PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-20260926.md
pole_id: POLE-KG-TDC-001
owner: L2-PLATFORM
repo: gerivdb/KIX
related_adr: ADR-2026-05-14-003-CMD-WRAPPER-FOR-POWERSHELL, ADR-2026-07-27-016-kix-orchestrator
related_moc: PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-20260926.md, PRD-MOC-KIX-MASTER-20260926.md
---

# PRD-MOC - KIX × GOVERNANCE-HUB Integration

## Résumé Exécutif

Intégration de KIX avec GOVERNANCE-HUB (L0-CANON) pour agréger les registres, valider les ADR/PRD-MOC/INTENT, et respecter la BDCP sur tous les appels.

**Statut** : **draft** (2026-09-30)

---

## 1. Interface

### 1.1 Client GOVERNANCE-HUB

**Fichier** : `src/governance_hub_client.py`
**Protocole** : REST + YAML parsing
**Health check** : `GET /health/governance-hub`
**Timeout** : 5s (configurable)

### 1.2 Méthodes

| Méthode | Paramètres | Retour | Description |
|---------|------------|--------|-------------|
| `get_registry(registry_name)` | registry_name: str | dict | Récupère un registre YAML |
| `validate_adr(adr_path)` | adr_path: str | bool | Valide un ADR |
| `validate_prd_moc(path)` | path: str | bool | Valide un PRD-MOC |
| `health()` | — | dict | Vérifie la santé du service |

---

## 2. Intégrations KIX

### 2.1 Agrégation des registres

```python
from governance_hub_client import GovernanceHubClient

client = GovernanceHubClient()
repos = client.get_registry("known_repositories")
```

### 2.2 Validation des documents

```python
is_valid = client.validate_adr("ADR-2026-09-28-001-WIN32-HIDDEN-WINDOW-ENFORCEMENT.md")
```

---

## 3. Critères d'Acceptation

- [ ] `GovernanceHubClient` implémenté avec méthodes `get_registry`, `validate_adr`, `validate_prd_moc`, `health`
- [ ] Tests unitaires pour chaque méthode (mock HTTP + YAML parsing)
- [ ] Health check intégré dans `diagnostics.py::run_all_checks()`
- [ ] Respect BDCP : pas de `gh`, pas de GitHub Actions
- [ ] Timeout configurable (défaut 5s)
- [ ] Logging WAL des validations

---

## 4. Proof-of-Life

- [ ] 2026-09-30T04:35:00+02:00 — Client GOVERNANCE-HUB créé et testé

## 5. Références

- Parent : `PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-20260926.md`
- Master : `PRD-MOC-KIX-MASTER-20260926.md`
