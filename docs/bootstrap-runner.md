# Bootstrap Runner Documentation

## Overview

The bootstrap runner is a dedicated Python service integrated into KIX that orchestrates the system startup sequence for the gerivdb ecosystem.

**Port**: 8810  
**Service**: `bootstrap`  
**Role**: Bootstrap orchestrator  
**Status**: Active (PRD-MOC-GEN-002 implemented, S1+S2+closure)  
**Strate**: L2-PLATFORM

## Endpoints

| Endpoint | Method | Description | Response |
|----------|--------|-------------|----------|
| `/health` | GET | Basic health check | `200 OK` |
| `/bootstrap/status` | GET | Detailed status of all services | `200 OK` + JSON |
| `/bootstrap/ready` | GET | Check if system is ready | `200 OK` or `503 Service Unavailable` |
| `/bootstrap/start` | POST | Trigger manual startup | `202 Accepted` |
| `/bootstrap/register` | POST | Register a service in KIX (`{"name","port","status?"}`) | `200 OK` / `400` / `502` |
| `/bootstrap/monitor` | GET | One-shot monitoring report with alert status | `200 OK` or `503` |

## Self-Healing Watchdog

A daemon thread re-checks all dependencies every
`BOOTSTRAP_CHECK_INTERVAL` seconds (default **3**) and automatically
re-runs the startup sequence when a required dependency is down and no
sequence is already running. Measured recovery (kill WAZAA bus -> port
back up): **8.1 s**, under the PRD §11 target of 10 s. To decommission a
service permanently, stop the bootstrap runner itself first.

## Startup Sequence

```
ECOS CLI
  -> BDCP-CORE (gateway-manager)
  -> KIX (port 8800) starts in "bootstrap pending" mode
  -> bootstrap (port 8810) starts automatically
      -> CHECK: gateway-manager (port 9000)
      -> CHECK: KIX self-check (port 8800)
      -> START: Arbiter (port 8742) via start-git-arbiter.ps1 (CMD wrapper + port wait)
      -> START: wazaa KG-L bus (port 1873) via src/bus_runner.py
      -> START/CHECK: trixd (port 7243) via KIX internal channel (X-KIX-Bootstrap)
      -> CHECK: wazaa-mc mission control (port 5002, optional)
      -> CHECK: flex-api (port 8080, optional)
      -> REGISTER: register all services in KIX
      -> PUBLISH: /bootstrap/ready = true when all required deps are up
   -> ECOS CLI polls /bootstrap/ready (Invoke-BootstrapGate, budget 30s,
      escape hatch ECOS_SKIP_BOOTSTRAP=1)
   -> Ecosystem operational
```

Note (PRD-MOC-GEN-002 G1): the real WAZAA bus is `src/bus_runner.py`
listening on 1873 (`PORT_ASYNC`) and 8200 (`PORT_THREADS`, informational).
Port 5002 is the separate mission-control HTTP service (`wazaa-mc`).

## Lifecycle States

```
                    +----------+
                    | PENDING  | <- KIX starts, waits for bootstrap
                    +----+-----+
                         |
                    +----+-----+
                    | CHECKING | <- Checking prerequisites
                    +----+-----+
                         |
           +-------------+-------------+
           |             |             |
           v             v             v
     +----------+   +----------+   +----------+
     | STARTING |   |  READY   |   | FAILED   |
     | (start   |   | (all     |   | (critical|
     | services)|   | services |   |  blocker)|
     +----------+   | running) |   +----------+
                    +----------+
```

## Configuration

In `config/runners.yaml`:

```yaml
- name: bootstrap
  runner_type: python
  port: 8810
  working_dir: D:/DO/WEB/TOOLS/L2-PLATFORM/KIX
  entrypoint: services/bootstrap_runner.py
  bootstrap: true
  auto_start: true
  health_path: /health
  restart_policy: on-failure
  log_file: D:/DO/WEB/TOOLS/L2-PLATFORM/KIX/logs/bootstrap.log
  dependencies:
    - gateway-manager
    - kix
    - arbiter
    - trixd
    - wazaa
    - flex-api
  kgl_schema: schemas/runners/bootstrap-status.schema.json
  meta:
    repo: gerivdb/GOVERNANCE-HUB
    role: bootstrap orchestrator
    intent_hash: 0xINTENT_BOOTSTRAP_RUNNER_GOVERNANCE_20260820
```

## Security

- **BDCP inviolable**: The bootstrap runner never calls `POST /clapet/open`.
- **Secrets**: Never stored in plain text in `runners.yaml`. Resolved via environment variables or system keyring.
- **SecretResolver**: Reads from `$env:VAR` or `keyring.get_password("gerivdb", var_name)`.

## Integration with ECOS CLI

ECOS CLI (`C:\DevTools\bin\ecos.ps1`) polls `/bootstrap/ready` after starting KIX:

```powershell
$bootstrapUrl = "http://127.0.0.1:8810/bootstrap/ready"
$bootstrapReady = $false
for ($i = 1; $i -le 30; $i++) {
    try {
        $resp = Invoke-RestMethod -Uri $bootstrapUrl -Method Get -TimeoutSec 1 -ErrorAction SilentlyContinue
        if ($resp -and $resp.ready -eq $true) {
            Write-Host "[BOOTSTRAP] Ready: all services operational" -ForegroundColor Green
            $bootstrapReady = $true
            break
        }
    } catch {
        # bootstrap not ready yet
    }
    Write-Host "[BOOTSTRAP] Waiting for bootstrap... ($i/30)" -ForegroundColor Yellow
    Start-Sleep -Seconds 1
}
if (-not $bootstrapReady) {
    Write-Host "[BOOTSTRAP] DEGRADED: bootstrap did not become ready in time" -ForegroundColor Red
}
```

## Monitoring

### Endpoint de monitoring

| Endpoint | Method | Description | Response |
|----------|--------|-------------|----------|
| `/bootstrap/monitor` | GET | Monitoring d'alerte | `200 OK` ou `503` + JSON |

### Script de monitoring

```bash
python scripts/bootstrap_monitor.py --once
python scripts/bootstrap_monitor.py --loop --interval 30
```

### Alertes générées

- `bootstrap failed` : phase FAILED
- `bootstrap blockers: ...` : blockers présents
- `bootstrap not ready` : pas prêt hors phase PENDING

### Intégration KIX

L'endpoint `/bootstrap/monitor` peut être interrogé par KIX pour détecter les défaillances bootstrap et déclencher des alertes via le système de notifications existant.

## Runbook

Le runbook complet est disponible dans `docs/runbook-bootstrap.md`.

**Procédure rapide de relance** :

```powershell
# 1. Vérifier l'état
Invoke-RestMethod -Uri "http://127.0.0.1:8810/bootstrap/status" -Method Get

# 2. Redémarrer via KIX
Invoke-RestMethod -Uri "http://127.0.0.1:8800/runners/bootstrap/restart" -Method Post -Headers @{"Authorization"="Bearer <TOKEN>"}

# 3. Vérifier
Invoke-RestMethod -Uri "http://127.0.0.1:8810/bootstrap/ready" -Method Get
```

## Testing

```bash
# Unit tests
pytest tests/test_bootstrap_runner.py -v

# Integration tests
pytest tests/test_bootstrap_kix_integration.py -v

# E2E tests
pytest tests/test_bootstrap_e2e.py -v

# Validation ENV2
python tests/validate_bootstrap_env2.py

# Validation PHI_TOTAL
python tests/validate_phi_total.py
```

## References

- **PRD**: `PRD-MOC-BOOTSTRAP-RUNNER-GOVERNANCE-2026-08-20.md`
- **INTENT**: `INTENT-BOOTSTRAP-RUNNER-GOVERNANCE-2026-08-20.md`
- **ADR**: `ADR-2026-08-20-001-bootstrap-runner.md`
- **Runbook**: `docs/runbook-bootstrap.md`
- **Monitoring**: `scripts/bootstrap_monitor.py`
- **KIX**: `D:\DO\WEB\TOOLS\L2-PLATFORM\KIX`
- **ECOS CLI**: `C:\DevTools\bin\ecos.ps1`
