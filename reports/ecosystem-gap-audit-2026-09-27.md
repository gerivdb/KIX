# KIX Ecosystem Gap Audit — 2026-09-27

## Structured Summary

- **Total runners**: 60
- **Runners with implementation**: 60 (all have generic runner wrappers)
- **Runners missing implementation**: 0 generic, 2 specific entrypoints missing (anamorphoser, tlm-lang)
- **Endpoints unprotected**: 29
- **plix dual-role status**: FOUND (service.py line 94)
- **meta.role coverage**: 60/60 (100%)

## 1. Runners Overview

### 1.1 Complete Runner List (60 runners)

| Name | Type | Port | Repo | Role | Working Dir | Implementation Status |
|------|------|------|------|------|-------------|----------------------|
| kg-l-coherence-watchdog | python | 8841 | gerivdb/KIX | operational | (none) | generic wrapper |
| nodex | python | 8821 | gerivdb/KIX | cognitive | (none) | generic wrapper |
| rootx | python | 8823 | gerivdb/KIX | cognitive | (none) | generic wrapper |
| talex | python | 8822 | gerivdb/KIX | cognitive | (none) | generic wrapper |
| friction-analyzer | python | 8815 | gerivdb/KIX | cognitive | (none) | generic wrapper |
| agent-manager | gateway-exe | 18001 | gerivdb/KIX | orchestrator | (none) | generic wrapper |
| llm-gateway | gateway-exe | 18000 | gerivdb/ECOS-CLI | llm-gateway | D:/DO/WEB/TOOLS/L1-INFRA/ECOS-CLI | EXISTS |
| batmcp | gateway-exe | 8000 | gerivdb/BatMCP | mcp-server | D:/DO/WEB/TOOLS/L4-TOOLS/BatMCP | EXISTS |
| kix | python | 8800 | gerivdb/KIX | orchestrator | D:/DO/WEB/TOOLS/L2-PLATFORM/KIX | EXISTS |
| bootstrap | python | 8810 | gerivdb/KIX | bootstrap orchestrator | D:/DO/WEB/TOOLS/L2-PLATFORM/KIX | EXISTS |
| rlm-metrics | python | 8802 | gerivdb/KIX | metrics collector | D:/DO/WEB/TOOLS/L2-PLATFORM/KIX | EXISTS |
| rlm-config | python | 8794 | gerivdb/KIX | configuration service | D:/DO/WEB/TOOLS/L2-PLATFORM/KIX | EXISTS |
| rlm-deploy | python | 8795 | gerivdb/KIX | deployment service | D:/DO/WEB/TOOLS/L2-PLATFORM/KIX | EXISTS |
| rlm-graph | python | 8797 | gerivdb/KIX | graph service | D:/DO/WEB/TOOLS/L2-PLATFORM/KIX | EXISTS |
| rlm-secure | python | 8796 | gerivdb/KIX | security service | D:/DO/WEB/TOOLS/L2-PLATFORM/KIX | EXISTS |
| rlm-incident | python | 8798 | gerivdb/KIX | incident service | D:/DO/WEB/TOOLS/L2-PLATFORM/KIX | EXISTS |
| rlm-release | python | 8799 | gerivdb/KIX | release service | D:/DO/WEB/TOOLS/L2-PLATFORM/KIX | EXISTS |
| kg-l | python | 8888 | gerivdb/KG-L | knowledge-graph service | D:/DO/WEB/TOOLS/L4-TOOLS/KG-L | EXISTS |
| jevx | node | 8889 | gerivdb/JEVX | decision-engine | D:/DO/WEB/TOOLS/L4-TOOLS/JEVX | EXISTS |
| flex-rust | rust | 7718 | gerivdb/FLEX | rust-service | D:/DO/WEB/TOOLS/L4-TOOLS/FLEX | EXISTS |
| go-service | go | 7717 | gerivdb/GO-SERVICE | go-service | D:/DO/WEB/TOOLS/L4-TOOLS/GO-SERVICE | MISSING |
| node-service | node | 7716 | gerivdb/NODE-SERVICE | node-service | D:/DO/WEB/TOOLS/L4-TOOLS/NODE-SERVICE | MISSING |
| kix-ecosystem | python | 8811 | gerivdb/KIX | ecosystem-orchestrator | D:/DO/WEB/TOOLS/L2-PLATFORM/KIX | EXISTS |
| wazaa-bus | python | 1874 | gerivdb/WAZAA | event-bus | D:/DO/WEB/TOOLS/L4-TOOLS/WAZAA | EXISTS |
| trixd | zig-binary | 7243 | gerivdb/TRIX | zig-runtime | D:/DO/WEB/TOOLS/L4-TOOLS/TRIX | EXISTS |
| gitex | custom | 0 | gerivdb/gitex | governance | (none) | generic wrapper |
| repoxt | custom | 0 | gerivdb/repoxt | governance | (none) | generic wrapper |
| syncx | custom | 0 | gerivdb/syncx | governance | (none) | generic wrapper |
| referex | custom | 0 | gerivdb/referex | governance | (none) | generic wrapper |
| kglx | custom | 0 | gerivdb/kglx | governance | (none) | generic wrapper |
| harnex | custom | 0 | gerivdb/harnex | governance | (none) | generic wrapper |
| telox | custom | 0 | gerivdb/telox | cognitive | (none) | generic wrapper |
| timx | custom | 0 | gerivdb/timx | cognitive | (none) | generic wrapper |
| rlm243 | custom | 0 | gerivdb/rlm243 | operational | (none) | generic wrapper |
| causex | custom | 0 | gerivdb/causex | cognitive | (none) | generic wrapper |
| morphex | custom | 0 | gerivdb/morphex | cognitive | (none) | generic wrapper |
| identx | custom | 0 | gerivdb/identx | cognitive | (none) | generic wrapper |
| topex | custom | 0 | gerivdb/topex | cognitive | (none) | generic wrapper |
| chronox | custom | 0 | gerivdb/chronox | cognitive | (none) | generic wrapper |
| llux-match | custom | 0 | gerivdb/llux-match | cognitive | (none) | generic wrapper |
| llux-index | custom | 0 | gerivdb/llux-index | cognitive | (none) | generic wrapper |
| wazaa | python | 5002 | gerivdb/wazaa | dashboard | D:/DO/WEB/TOOLS/L4-TOOLS/WAZAA | EXISTS |
| flex-api | python | 8080 | gerivdb/flex-api | api | D:/DO/WEB/TOOLS/L4-TOOLS/FLEX | EXISTS |
| prognex | custom | 0 | gerivdb/prognex | cognitive | (none) | generic wrapper |
| llux-learn | custom | 0 | gerivdb/llux-learn | cognitive | (none) | generic wrapper |
| llux-replay | custom | 0 | gerivdb/llux-replay | cognitive | (none) | generic wrapper |
| timx-feature-store | custom | 0 | gerivdb/timx-feature-store | operational | (none) | generic wrapper |
| rlm-mdu | custom | 0 | gerivdb/rlm-mdu | operational | (none) | generic wrapper |
| deployex | custom | 0 | gerivdb/deployex | cognitive | (none) | generic wrapper |
| flowx | custom | 0 | gerivdb/flowx | cognitive | (none) | generic wrapper |
| llm-core | custom | 0 | gerivdb/llm-core | llm | (none) | generic wrapper |
| piano | custom | 0 | gerivdb/piano | operational | (none) | generic wrapper |
| trix | custom | 0 | gerivdb/trix | operational | (none) | generic wrapper |
| conversation-cognitive | custom | 0 | gerivdb/conversation-cognitive | cognitive | (none) | generic wrapper |
| flex | custom | 0 | gerivdb/flex | infrastructure | (none) | generic wrapper |
| infx | custom | 0 | gerivdb/infx | citizen | (none) | generic wrapper |
| codedb-e5620 | custom | 0 | gerivdb/codedb-e5620 | infrastructure | (none) | generic wrapper |
| nexus | custom | 8801 | gerivdb/nexus | governance | D:/DO/WEB/TOOLS/L1-INFRA/NEXUS | EXISTS |
| anamorphoser | python | 8831 | gerivdb/anamorphoser | cognitive | D:\DO\WEB\TOOLS\L0-CANON\GOVERNANCE-HUB | entrypoint MISSING |
| tlm-lang | python | 8803 | gerivdb/tlm-lang | cognitive | D:\DO\WEB\TOOLS\L0-CANON\unified-design\designs\tlm-lang | entrypoint MISSING |

### 1.2 Runners with Implementation

- **Generic implementations**: 60/60 (all runner types have generic wrappers: python_runner.py, node_runner.py, rust_runner.py, go_runner.py, zig_runner.py, gateway_runner.py, custom_runner.py)
- **Specific implementations**: 11/60 (runners with specific logic in runners/ subdirectories)
  - auto-index, auto-narrative, deploy-runner, graph-versioning, health-check, ingestor, kg-l-sync, nexus-sync, talex-narrate, talex-postmortem, wazaa-relay

### 1.3 Runners Missing Implementation

- **Generic**: 0
- **Specific entrypoints missing**: 2
  - anamorphoser: runners/anamorphoser_fastapi.py (MISSING)
  - tlm-lang: runners/tlm_lang_fastapi.py (MISSING)

### 1.4 Runners Pointing to Non-Existent Repos

- go-service: D:/DO/WEB/TOOLS/L4-TOOLS/GO-SERVICE (MISSING)
- node-service: D:/DO/WEB/TOOLS/L4-TOOLS/NODE-SERVICE (MISSING)

## 2. Endpoint Protection Analysis

### 2.1 Unprotected Endpoints (29 total)

| Method | Path | Handler | Risk |
|--------|------|---------|------|
| GET | /health | health | LOW |
| GET | /healthz | healthz | LOW |
| GET | /health/kix | health_kix | LOW |
| GET | /health/l3 | health_l3 | LOW |
| POST | /health/l3 | register_l3_health | MEDIUM |
| GET | /readyz | readyz | LOW |
| GET | /preflight/status | preflight_status | MEDIUM |
| POST | /preflight/assert | preflight_assert | HIGH |
| POST | /login | login | N/A |
| GET | /metrics | metrics | MEDIUM |
| GET | /metrics/prometheus | metrics_prometheus | LOW |
| GET | /vote | vote | LOW |
| GET | /runners | list_runners | MEDIUM |
| GET | /status/cross-service | cross_service_status | MEDIUM |
| POST | /runners/register | register_runner | HIGH |
| POST | /schedule/cycle | schedule_cycle | HIGH |
| GET | /schedules | list_schedules | MEDIUM |
| GET | /doctor | doctor | MEDIUM |
| POST | /doctor/run | doctor_run | HIGH |
| POST | /doctor/restore | doctor_restore | HIGH |
| GET | /swarm/status | swarm_status | MEDIUM |
| GET | /probe/audit | probe_audit | MEDIUM |
| GET | /audit | action_audit | HIGH |
| GET | /alerts | alerts | MEDIUM |
| GET | /events | events | LOW |
| GET | /notifications/history | notifications_history | MEDIUM |
| GET | /remediation/status | remediation_status | HIGH |
| GET | /dashboard | dashboard | MEDIUM |
| POST | /process/release-handles | release_handles | HIGH |

### 2.2 Protected Endpoints (10 total)

- POST /runners/<name>/start (@login_required + @requires_capability)
- POST /runners/<name>/stop (@login_required + @requires_capability)
- POST /runners/<name>/restart (@login_required + @requires_capability)
- GET /runners/<name>/health (unprotected but read-only)
- GET /runners/<name>/logs (unprotected but read-only)
- POST /schedule/cycle (@login_required + @requires_capability)
- DELETE /schedule/cycle/<id> (@login_required + @requires_capability)
- GET /schedules (@login_required + @requires_capability)
- POST /doctor/run (@login_required + @requires_capability)
- POST /doctor/restore (@login_required + @requires_capability)

## 3. PLIX Dual-Role Status

**Status**: FOUND

**Location**: service.py line 94

**Code**:
```python
"dual_role": port in SERVICE_MAP  # TRIX, PLIX sont aussi RLM
```

**Context**: PLIX (port 8788) is handled as a dual-role service in the legacy service.py. It appears in both:
- SERVICE_MAP (RLM family)
- TLM_SERVICE_MAP (TLM family)

**Coverage**: The dual-role pattern is only documented in service.py. It is not explicitly handled in the modern runners.yaml or src/app.py runner registry.

## 4. Meta.Role Coverage

- **Total runners with meta.role**: 60/60 (100%)
- **Role categories**:
  - operational: 5
  - cognitive: 21
  - orchestrator: 2
  - llm-gateway: 1
  - mcp-server: 1
  - bootstrap orchestrator: 1
  - metrics collector: 1
  - configuration service: 1
  - deployment service: 1
  - graph service: 1
  - security service: 1
  - incident service: 1
  - release service: 1
  - knowledge-graph service: 1
  - decision-engine: 1
  - rust-service: 1
  - go-service: 1
  - node-service: 1
  - ecosystem-orchestrator: 1
  - event-bus: 1
  - zig-runtime: 1
  - governance: 6
  - dashboard: 1
  - api: 1
  - llm: 1
  - operational: 3
  - infrastructure: 2
  - citizen: 1
  - infrastructure: 1

## 5. Gap Summary

### 5.1 Critical Gaps (High Priority)

| Priority | Gap | Impact | Effort |
|----------|-----|--------|--------|
| P0 | go-service repo path missing | Service cannot start | Medium |
| P0 | node-service repo path missing | Service cannot start | Medium |
| P0 | anamorphoser entrypoint missing | Runner cannot start | Low |
| P0 | tlm-lang entrypoint missing | Runner cannot start | Low |

### 5.2 Medium Priority Gaps

| Priority | Gap | Impact | Effort |
|----------|-----|--------|--------|
| P1 | 6 runners with no working_dir | Cannot start via generic wrapper | Low |
| P1 | 29 unprotected endpoints | Security exposure | Medium |
| P2 | PLIX dual-role only in legacy service.py | Not in modern runner registry | Low |

### 5.3 Low Priority Gaps

| Priority | Gap | Impact | Effort |
|----------|-----|--------|--------|
| P2 | Specific runner implementations not mapped to runners.yaml | Maintenance overhead | Low |
| P2 | Generic runner wrappers for all custom runners | May need specific implementations | Low |

## 6. Top 5 Priority Gaps to Fix

1. **go-service and node-service repo paths missing** — These runners reference D:/DO/WEB/TOOLS/L4-TOOLS/GO-SERVICE and D:/DO/WEB/TOOLS/L4-TOOLS/NODE-SERVICE which do not exist. Either create the repos or remove from runners.yaml.

2. **anamorphoser and tlm-lang entrypoint implementations missing** — These runners declare entrypoints (runners/anamorphoser_fastapi.py and runners/tlm_lang_fastapi.py) but the files do not exist. Either create the files or remove the entrypoint declarations.

3. **29 unprotected endpoints** — Many read-only endpoints are unprotected. Consider adding @login_required or @requires_capability to sensitive endpoints like /audit, /doctor/run, /doctor/restore, /process/release-handles.

4. **6 runners with no working_dir** — kg-l-coherence-watchdog, nodex, rootx, talex, friction-analyzer, agent-manager have no working_dir defined. This prevents them from being started via the generic runner wrapper.

5. **PLIX dual-role not in modern registry** — The dual-role pattern for PLIX/TRIX is only documented in legacy service.py. Consider adding dual-role metadata to the modern runners.yaml or creating a specific runner implementation.

## 7. Recommendations

1. **Immediate**: Fix go-service and node-service paths or remove from runners.yaml
2. **Immediate**: Create missing entrypoint files for anamorphoser and tlm-lang, or remove entrypoint declarations
3. **Short-term**: Add working_dir to the 6 runners that are missing it
4. **Short-term**: Protect sensitive endpoints with @login_required or @requires_capability
5. **Medium-term**: Document the PLIX dual-role pattern in the modern runner registry
6. **Medium-term**: Create specific runner implementations for runners that currently rely on generic wrappers
