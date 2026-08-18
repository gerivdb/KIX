# Validation Cross-Repo — KIX Generic Runner Wrapper

Date : 2026-08-18
Statut : Phase 1-4 codées et testées unitairement, runtime validation en attente (sauf BUZZ-X bloqué)

## Résumé

L'architecture KIX Generic Runner Wrapper est codée et testée unitairement dans KIX.
Les runners suivants sont déclarés dans `config/runners.yaml` :

| Runner | Type | Repo | Tests unitaires | Validation runtime |
|--------|------|------|-----------------|-------------------|
| `kix` | python | KIX | ✅ 134 passed | ✅ KIX lui-même |
| `gateway-manager` | gateway-exe | GATEWAY-MANAGER | ✅ 11 passed | ⏳ Phase 2 (GM doit être lancé) |
| `trixd` | zig-binary | TRIX | ✅ 7 passed | ⏳ Phase 3 (zig build trixd requis) |
| `wazaa` | python | WAZAA | ✅ 4 passed | ⏳ Phase 4 (server.py doit démarrer) |
| `buzz` | python | BUZZ-X | ❌ N/A | ❌ Phase 4 bloquée (non fonctionnel) |

## Validation statique

```powershell
cd D:/DO/WEB/TOOLS/L2-PLATFORM/KIX
python scripts/validate_runners.py
```

Sortie attendue :
```
[CHECK] kix (python)
  [OK] entrypoint: D:\DO\WEB\TOOLS\L2-PLATFORM\KIX\src\app.py
  [OK] port=8800 health=/healthz
[CHECK] gateway-manager (gateway-exe)
  [OK] command: gateway-manager start --port 9000
  [OK] port=9000 health=/health
[CHECK] trixd (zig-binary)
  [OK] binary: D:\DO\WEB\TOOLS\L4-TOOLS\TRIX\zig-out\bin\trixd.exe
  [INFO] build pre_start: ['zig', 'build', 'trixd']
  [OK] port=7243 health=/healthz
[CHECK] wazaa (python)
  [OK] entrypoint: D:\DO\WEB\TOOLS\L4-TOOLS\WAZAA\tools\mission_control\server.py
  [OK] port=5002 health=/healthz
```

## Procédure de validation par repo

### GATEWAY-MANAGER (Phase 2)

**Prérequis** : GATEWAY-MANAGER installé et accessible via CLI `gateway-manager`.

1. Démarrer GATEWAY-MANAGER manuellement :
   ```powershell
   cd D:/DO/WEB/TOOLS/L1-INFRA/GATEWAY-MANAGER
   gateway-manager start --port 9000
   ```

2. Vérifier le health-check :
   ```powershell
   curl http://localhost:9000/health
   ```

3. Tester le wrapper KIX :
   ```powershell
   cd D:/DO/WEB/TOOLS/L2-PLATFORM/KIX
   python scripts/validate_runners.py --runner gateway-manager --start
   ```

4. Vérifier le statut dans KIX :
   ```powershell
   curl http://localhost:8800/runners/gateway-manager/health
   curl http://localhost:8800/swarm/status
   ```

5. Arrêter :
   ```powershell
   python scripts/validate_runners.py --stop
   ```

**Validation attendue** :
- `gateway-manager` apparaît dans `/swarm/status`
- Health-check retourne `status: ok`
- `restart_policy: always` fonctionne (redémarre si crash)

### TRIX (Phase 3)

**Prérequis** : Zig 0.15 installé, `zig build trixd` fonctionne.

1. Vérifier que le binaire existe :
   ```powershell
   Test-Path D:\DO\WEB\TOOLS\L4-TOOLS\TRIX\zig-out\bin\trixd.exe
   ```

2. Compiler si nécessaire :
   ```powershell
   cd D:/DO/WEB/TOOLS/L4-TOOLS/TRIX
   zig build trixd
   ```

3. Tester le wrapper KIX (build automatique) :
   ```powershell
   cd D:/DO/WEB/TOOLS/L2-PLATFORM/KIX
   python scripts/validate_runners.py --runner trixd --start
   ```

4. Vérifier le statut dans KIX :
   ```powershell
   curl http://localhost:8800/runners/trixd/health
   curl http://localhost:8800/swarm/status
   ```

5. Arrêter :
   ```powershell
   python scripts/validate_runners.py --stop
   ```

**Validation attendue** :
- `trixd` apparaît dans `/swarm/status`
- Health-check sur port 7243 retourne `status: ok`
- Build automatique `zig build trixd` s'exécute avant le start
- `restart_policy: on-failure` fonctionne

### WAZAA (Phase 4)

**Prérequis** : WAZAA opérationnel, `tools/mission_control/server.py` démarre sur port 5002.

1. Démarrer WAZAA manuellement (pour vérifier) :
   ```powershell
   cd D:/DO/WEB/TOOLS/L4-TOOLS/WAZAA
   python tools/mission_control/server.py
   ```

2. Vérifier le health-check :
   ```powershell
   curl http://localhost:5002/healthz
   ```

3. Tester le wrapper KIX :
   ```powershell
   cd D:/DO/WEB/TOOLS/L2-PLATFORM/KIX
   python scripts/validate_runners.py --runner wazaa --start
   ```

4. Vérifier le statut dans KIX :
   ```powershell
   curl http://localhost:8800/runners/wazaa/health
   curl http://localhost:8800/swarm/status
   ```

5. Arrêter :
   ```powershell
   python scripts/validate_runners.py --stop
   ```

**Validation attendue** :
- `wazaa` apparaît dans `/swarm/status`
- Health-check sur port 5002 retourne `status: ok`
- WAZAA ne dépend PAS de BUZZ-X

### BUZZ-X (Phase 4 — BLOQUÉ)

**Statut** : ❌ NON FONCTIONNEL — `busrunner.py` non opérationnel.

**Blocant** : Gate P-110 — BUZZ-X doit être fonctionnel avant intégration dans KIX.

**Action requise** : Réparer `scripts/busrunner.py` dans `D:\DO\WEB\TOOLS\L4-TOOLS\BUZZ-X`.

**Une fois réparé** :
1. Démarrer `busrunner.py` manuellement
2. Vérifier le health-check sur port 60001
3. Décommenter l'entrée `buzz` dans `config/runners.yaml`
4. Tester le wrapper KIX :
   ```powershell
   python scripts/validate_runners.py --runner buzz --start
   ```

## Tests unitaires

```powershell
cd D:/DO/WEB/TOOLS/L2-PLATFORM/KIX
python -m pytest tests/ -q -k "not test_known_repositories_loader"
```

**Résultat** : 165 passed, 2 skipped, 1 deselected (pré-existant worktree).

Couverture :
- `tests/test_runners.py` : 21 tests — RunnerSpec, Registry, PythonRunner, ZigBinaryRunner, GatewayRunner
- `tests/test_runners_integration.py` : 9 tests — lifecycle runners + endpoints `/swarm/status`, `/doctor`, `/doctor/run`
- `tests/test_gateway_runner_phase2.py` : 11 tests — GatewayRunner CLI, health, logs, restart, bootstrap
- `tests/test_trix_runner_phase3.py` : 7 tests — ZigBinaryRunner build pre_start, health, logs
- `tests/test_wazaa_runner_phase4.py` : 4 tests — PythonRunner WAZAA, dépendance kix uniquement (pas buzz)

## Gates

| Gate | Critère | Statut |
|------|---------|--------|
| P-108 | ADR accepted par tous les leads | ⏳ En attente |
| P-109 | Phase 1 implémentée et testée | ✅ Code prêt, tests passent |
| P-110 | BUZZ-X fonctionnel avant intégration dans KIX | ❌ Bloquant — BUZZ-X non fonctionnel |

## Références

- **ADR** : `ADR-2026-08-18-002-KIX-GENERIC-RUNNER-WRAPPER.md`
- **PRD MOC Principal** : `PRD-MOC-KIX-GENERIC-RUNNER-WRAPPER-2026-08-18.md` (TRIX)
- **PRD MOC KIX** : `PRD-MOC-KIX-ORCHESTRATOR-2026-08-18.md` (KIX)
- **PRD MOC GATEWAY-MANAGER** : `PRD-MOC-GATEWAY-MANAGER-RUNNER-2026-08-18.md`
- **PRD MOC TRIX** : `PRD-MOC-TRIX-ZIG-RUNNER-2026-08-18.md`
- **PRD MOC WAZAA** : `PRD-MOC-WAZAA-KIX-RUNNER-2026-08-18.md`
- **PRD MOC BUZZ-X** : `PRD-MOC-BUZZ-X-KIX-INTEGRATION-2026-08-18.md`
