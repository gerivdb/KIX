# KIX Diagnostics API Documentation

**IntentHash** : `0xPRD_MOC_AGENT_MANAGER_DIAGNOSTICS_ECOSYSTEM_20260809`
**Port** : 8800

---

## Endpoint

### GET /agent-manager/diagnostics

Retourne un diagnostic complet de l'environnement Agent Manager.

#### Réponse 200

```json
{
  "timestamp": "2026-08-09T19:00:00Z",
  "overall": "PASS",
  "summary": "4 checks, 0 failed, 0 warnings",
  "checks": {
    "cli_presence": {
      "status": "PASS",
      "message": "CLI kilocode found",
      "path": "C:\\Users\\GG\\.kilocode\\bin\\kilocode.cmd",
      "version": "0.9.9"
    },
    "auth_status": {
      "status": "PASS",
      "message": "Authentication valid"
    },
    "providers_config": {
      "status": "PASS",
      "message": "2 provider(s) configured",
      "providers": ["Kilo Gateway", "OpenAI"]
    },
    "trix_binary": {
      "status": "PASS",
      "message": "TRIX binary accessible",
      "path": "D:\\DO\\WEB\\TOOLS\\L4-TOOLS\\TRIX\\trix.exe",
      "version": "0.15.0"
    }
  },
  "duration_ms": 342
}
```

#### Réponse 503

Retourné si un check FAIL existe.

```json
{
  "timestamp": "2026-08-09T19:00:00Z",
  "overall": "FAIL",
  "summary": "4 checks, 1 failed, 0 warnings",
  "checks": {
    "cli_presence": {
      "status": "FAIL",
      "message": "CLI kilocode not found in PATH",
      "hint": "npm install -g @kilocode/cli"
    }
  },
  "duration_ms": 120
}
```

## Intégration

- **KIX service.py** : ajouter route `/agent-manager/diagnostics`
- **REPO.yaml** : ajouter endpoint dans la description
- **ONTOLOGY_DECLARATION.yaml** : ajouter concept `agent-manager-diagnostics`

## Référence ADR

- **ADR** : ADR-2026-08-09-002-AGENT-MANAGER-DIAGNOSTICS
- **IntentHash** : `0xPRD_MOC_AGENT_MANAGER_DIAGNOSTICS_ECOSYSTEM_20260809`
- **Dépôt** : gerivdb/GOVERNANCE-HUB
- **Statut ADR** : proposed
- **Màj requise si** : statut ADR passe à deprecated ou superseded
