---
type: "PRD_MOC"
version: "1.0.0"
date: "2026-09-27"
updated: "2026-09-28"
status: "implemented"
intent_hash: "0xKIX_TRIX_INTEGRATION_20260927"
parent_doc: PRD-MOC-KIX-ECOSYSTEM-INTEGRATION-MASTER-2026-09-27.md
related_adr: ADR-2026-08-18-002-KIX-GENERIC-RUNNER-WRAPPER.md, ADR-2026-07-28-001-tlm-lang-runner
related_moc: PRD-MOC-KIX-MASTER.md, PRD-MOC-KIX-MULTI-LANG-ECOSYSTEM-2026-09-24.md
---

# PRD MOC - KIX - Intégration TRIX

## 1. RÉSUMÉ EXÉCUTIF

Ce PRD MOC couvre l'intégration de **TRIX** (gerivdb/TRIX) dans KIX comme runner de type `zig-binary`.

**Rôle** : Minimal Linux syscall dispatch runtime for Windows/WSL1 (HP Z600) -- Zig runtime
**Port** : 7243 (trixd), 0 (trix custom)
**Type** : zig-binary / custom
**Strate** : L4-TOOLS
**Statut** : ✅ **Intégré**

## 2. CONFIGURATION RUNNER

```yaml
- name: trixd
  runner_type: zig-binary
  port: 7243
  working_dir: D:/DO/WEB/TOOLS/L4-TOOLS/TRIX
  binary: trix.exe
  depends_on: [kix]
  restart_policy: always

- name: trix
  runner_type: custom
  working_dir: D:/DO/WEB/TOOLS/L4-TOOLS/TRIX
  depends_on: [kix]
  restart_policy: always
```

## 3. DUAL-ROLE PATTERN

TRIX/TRIXD/PLIX appartiennent à la fois aux familles **RLM** et **TLM** :

| Runner | Port | Familles | Description |
|--------|------|----------|-------------|
| `trixd` | 7243 | RLM + TLM | Runtime Zig dispatch |
| `trix` | 0 | RLM + TLM | Service TRIX (legacy) |
| `plix` | 8788 | RLM + TLM | LARQL-243 codec |

Source : `service.py` — `dual_role = port in SERVICE_MAP`

## 4. POINTS D'INTÉGRATION KIX

| Point | Protocole | Description |
|-------|-----------|-------------|
| KIX → TRIX | REST + WAZAA | Orchestration runners Zig |
| bootstrap → TRIX | TCP/HTTP | Vérification dépendance critique |
| KIX → PLIX | REST | LARQL codec integration |

## 5. ENDPOINTS UTILISÉS PAR KIX

| Endpoint | Méthode | Usage KIX |
|----------|---------|-----------|
| `/health` | GET | Health check |
| `/dispatch` | POST | Dispatch TLM requests |

## 6. CAPABILITY MODEL

| Runner | meta.role | Capabilities |
|--------|-----------|--------------|
| trixd | `zig-runtime` | `runner:start`, `runner:stop`, `runner:restart`, `health:check` |
| trix | `operational` | `runner:start`, `runner:stop` |

## 7. GOUVERNANCE

| Attribut | Valeur |
|----------|--------|
| **Repo** | gerivdb/TRIX |
| **Local Path** | `D:\DO\WEB\TOOLS\L4-TOOLS\TRIX` |
| **ADR** | ADR-2026-08-18-002-KIX-GENERIC-RUNNER-WRAPPER.md |
| **IntentHash** | 0xKIX_TRIX_INTEGRATION_20260927 |

## 8. PREUVE-OF-LIFE

- [x] 2026-09-27T23:00:00+02:00 — Runner `trixd` configuré dans `runners.yaml`
- [x] 2026-09-27T23:00:00+02:00 — ZigRunner implémenté dans `runners/zig_runner.py`
- [x] 2026-09-27T23:00:00+02:00 — Dual-role pattern documenté dans PRD-MOC-KIX-MASTER.md
- [x] 2026-09-27T23:00:00+02:00 — Capability model appliqué

## 9. RÉFÉRENCES

- `PRD-MOC-KIX-MASTER.md` : Master MOC KIX
- `PRD-MOC-KIX-MULTI-LANG-ECOSYSTEM-2026-09-24.md` : Multi-lang ecosystem
- `PRD-MOC-KIX-EXE-ORCHESTRATION-2026-09-24.md` : Exe orchestration
- `config/runners.yaml` : Configuration runner
- `runners/zig_runner.py` : Implémentation ZigRunner
- `service.py` : Legacy service map (dual_role)

---

**IntentHash** : `0xKIX_TRIX_INTEGRATION_20260927`
**Statut** : **implemented**
**Date** : 2026-09-27

*PRD-MOC-KIX-TRIX — implemented — 2026-09-27*
