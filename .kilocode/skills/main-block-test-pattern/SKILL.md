---
name: main-block-test-pattern
description: Pattern de test pour blocs __main__ via compile/exec avec injection de mocks. Résout les problèmes de coverage et d'exécution de scripts Python.
version: 1.0.0
intent_hash: 0xMAIN_BLOCK_TEST_PATTERN_20260930
---

# Main Block Test Pattern

## Objectif
Tester les blocs `if __name__ == "__main__"` sans processus enfant, en injectant les mocks nécessaires via `compile/exec`.

## Usage

```python
from pathlib import Path
from unittest.mock import patch

def test_main_block():
    # Lire le source
    source = Path("src/script.py").read_text(encoding="utf-8")
    code = compile(source, str(Path("src/script.py")), "exec")
    
    # Injecter les mocks dans les globals
    mock_run = MagicMock(return_value={"error": 0, "checks": []})
    with patch("sys.exit") as mock_exit:
        exec(code, {
            "__name__": "__main__",
            "__file__": str(Path("src/script.py")),
            "run_all_checks": mock_run,
        })
    
    mock_run.assert_called_once()
    mock_exit.assert_called_once_with(0)
```

## Points critiques

1. **`__file__` obligatoire** : certains scripts utilisent `Path(__file__)`
2. **Injection des mocks** : passer les mocks dans les globals du `exec`
3. **`sys.exit` patché** : éviter l'exit réel du processus
4. **Coverage** : utiliser `compile(source, filename, "exec")` pour que coverage associe l'exécution au fichier original

## Anti-patterns

- ❌ `subprocess.run([sys.executable, module_path])` sans `PYTHONPATH`
- ❌ Oublier `__file__` dans les globals
- ❌ Ne pas patcher `sys.exit` → le processus s'arrête

## Référence
- Incident : `ERR-COV-002` — Ligne bootstrap.py ligne 30 non couverte
- Module : `bootstrap.py`, `diagnostics.py`
- Tests : `tests/unit/test_runtime_bootstrap.py`, `tests/unit/test_diagnostics.py`
