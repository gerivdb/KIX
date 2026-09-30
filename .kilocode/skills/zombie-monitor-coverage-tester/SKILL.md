---
name: zombie-monitor-coverage-tester
description: Skill spécialisé pour tester la couverture de zombie_monitor.py et combler les gaps de couverture via tests ciblés WMI/psutil/purge/Flask routes. Utilise ATOM-KIX-ZOMBIE-MONITOR-COVERAGE-TEST-PATTERN.
version: 1.0.0
intent_hash: 0xSKILL_ZOMBIE_MONITOR_COVERAGE_TESTER_20260930
---

# Zombie Monitor Coverage Tester

## Objectif
Atteindre et maintenir ≥95% de couverture sur `src/zombie_monitor.py` via tests ciblés, en éliminant les erreurs de mock courantes (`ERR-KIX-001`, `ERR-KIX-002`, `ERR-KIX-003`, `ERR-KIX-004`).

## Usage

### Identification des gaps
```bash
pytest tests/ --cov=src --cov-report=term-missing -q
# Chercher: src/zombie_monitor.py N M P% missing_lines
```

### Pattern de mock WMI/psutil
```python
# ERR-KIX-001/002 fix: use patch.dict(sys.modules)
from unittest.mock import MagicMock, patch

def test_wmi_skip_non_zombie_name(monkeypatch):
    monkeypatch.setattr("sys.platform", "win32")
    fake_wmi = MagicMock()
    fake_proc = MagicMock()
    fake_proc.Name = "not_zombie.exe"
    fake_proc.ProcessId = 1111
    fake_wmi.Win32_Process.return_value = [fake_proc]
    # CORRECT: patch.dict on sys.modules
    with patch.dict("sys.modules", {"psutil": None, "wmi": fake_wmi}):
        result = get_process_zombies()
    assert result == []
```

### Pattern Flask app_context
```python
# ERR-KIX-003 fix: use app.app_context()
from flask import Flask

def test_list_zombies_summary():
    app = Flask(__name__)
    app.register_blueprint(zombie_bp)
    with app.app_context():
        # CORRECT: inside app context
        result = list_zombies().get_json()
    assert result["summary"]["total"] >= 0
```

### Pattern pytest-cov
```bash
# ERR-KIX-004 fix: use --cov=src (directory)
# INCORRECT: pytest --cov=src/zombie_monitor.py
# CORRECT: pytest --cov=src --cov-report=term-missing
```

## Checklist avant commit
- [ ] `pytest tests/ --cov=src --cov-report=term-missing -q` exécuté
- [ ] Coverage zombie_monitor.py ≥ 95%
- [ ] Pas d'ERR-KIX-001/002/003/004 dans les nouveaux tests
- [ ] Tests passent sur Windows et Linux

## Références
- Atome: `ATOM-KIX-ZOMBIE-MONITOR-COVERAGE-TEST-PATTERN`
- Atome: `ATOM-KIX-WMI-FALLBACK-TEST`
- Atome: `ATOM-KIX-ECOSYSTEM-CLIENT-MOCK`
- Atome: `ATOM-KIX-PYTEST-COV-MISSING-IDENTIFIER`
- Atome: `ATOM-KIX-COVERAGE-GAP-FILLER`
- Atome: `ATOM-KIX-FLASK-APP-CONTEXT-TEST`
- Atome: `ATOM-KIX-MONKEYPATCH-LIMITATION`
