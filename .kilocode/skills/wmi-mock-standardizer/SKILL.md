---
name: wmi-mock-standardizer
description: Standardise les mocks WMI pour les tests Windows. Utilise un mock imbriqué `wmi.WMI().Win32_Process()` avec tous les attributs nécessaires (Name, ProcessId, CreationDate, MainWindowTitle, CPU, WorkingSet64).
version: 1.0.0
intent_hash: 0xWMI_MOCK_STANDARDIZER_20260930
---

# WMI Mock Standardizer

## Objectif
Fournir un template de mock WMI standardisé pour les tests Windows, éliminant les erreurs de mock mal structuré (`ERR-MOCK-001`).

## Usage

```python
from unittest.mock import MagicMock

def create_wmi_mock(processes):
    """Crée un mock WMI standardisé."""
    fake_wmi = MagicMock()
    fake_wmi_instance = MagicMock()
    fake_procs = []
    for proc in processes:
        fake_proc = MagicMock()
        fake_proc.Name = proc["name"]
        fake_proc.ProcessId = proc["pid"]
        fake_proc.CreationDate = proc.get("creation_date", "20260920100000.000000+000")
        fake_proc.MainWindowTitle = proc.get("window_title", "")
        fake_proc.CPU = proc.get("cpu", 0.1)
        fake_proc.WorkingSet64 = proc.get("memory", 5 * 1024 * 1024)
        fake_procs.append(fake_proc)
    fake_wmi_instance.Win32_Process.return_value = fake_procs
    fake_wmi.WMI.return_value = fake_wmi_instance
    return fake_wmi
```

## Pattern de test

```python
def test_wmi_fallback():
    fake_wmi = create_wmi_mock([{"name": "git.exe", "pid": 1111}])
    with patch.dict("sys.modules", {"wmi": fake_wmi}):
        result = get_process_zombies()
    assert len(result) == 1
    assert result[0]["pid"] == 1111
```

## Anti-patterns

- ❌ `fake_wmi.Win32_Process.return_value` (manque `.WMI()`)
- ❌ Attributs manquants (`MainWindowTitle`, `CPU`, `WorkingSet64`)
- ❌ `CreationDate` sans format ISO

## Référence
- Incident : `ERR-MOCK-001` — Mock WMI mal structuré
- Module : `zombie_monitor.py`
- Test : `tests/unit/test_zombie_monitor.py::TestGetProcessZombiesWmi`
