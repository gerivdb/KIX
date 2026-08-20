# Bootstrap Runner Documentation

## Overview

The bootstrap runner is a dedicated Python service integrated into KIX that orchestrates the system startup sequence for the gerivdb ecosystem.

**Port**: 8810  
**Service**: `bootstrap`  
**Role**: Bootstrap orchestrator  
**Status**: Proposed  
**Strate**: L2-PLATFORM

## Endpoints

| Endpoint | Method | Description | Response |
|----------|--------|-------------|----------|
| `/health` | GET | Basic health check | `200 OK` |
| `/bootstrap/status` | GET | Detailed status of all services | `200 OK` + JSON |
| `/bootstrap/ready` | GET | Check if system is ready | `200 OK` or `503 Service Unavailable` |
| `/bootstrap/start` | POST | Trigger manual startup | `202 Accepted` |

## Startup Sequence

```
ECOS CLI
  -> BDCP-CORE (gateway-manager)
  -> KIX (port 8800) starts in "bootstrap pending" mode
  -> bootstrap (port 8810) starts automatically
      -> CHECK: gateway-manager (port 9000)
      -> CHECK: KIX self-check (port 8800)
      -> START: Arbiter (port 8742)
      -> START/CHECK: trixd (port 7243) with dynamic headers
      -> CHECK: wazaa (port 5002)
      -> CHECK: flex-api (port 8080)
      -> REGISTER: register all services in KIX
      -> PUBLISH: /bootstrap/ready = true
  -> ECOS CLI polls /bootstrap/ready
  -> Ecosystem operational
```

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

## Testing

```bash
# Unit tests
pytest tests/test_bootstrap_runner.py -v

# Integration tests
pytest tests/test_bootstrap_kix_integration.py -v

# All bootstrap tests
pytest tests/test_bootstrap_runner.py tests/test_bootstrap_kix_integration.py -v
```

## References

- **PRD**: `PRD-MOC-BOOTSTRAP-RUNNER-GOVERNANCE-2026-08-20.md`
- **INTENT**: `INTENT-BOOTSTRAP-RUNNER-GOVERNANCE-2026-08-20.md`
- **ADR**: `ADR-2026-08-20-001-bootstrap-runner.md`
- **KIX**: `D:\DO\WEB\TOOLS\L2-PLATFORM\KIX`
- **ECOS CLI**: `C:\DevTools\bin\ecos.ps1`
