---
name: PathMockingStrategy
description: Stratégie de mock pour pathlib.Path qui évite les pièges de Path.home() et des chemins absolus. Remplace les monkeypatch.setattr("Path.home", return_value=...) par des lambdas ou des substitutions de classe.
version: 1.0.0
intent_hash: 0xPATH_MOCKING_STRATEGY_20260930
---

# PathMocking Strategy

## Objectif
Éliminer les erreurs de mock `pathlib.Path` (`ERR-MOCK-002`) en fournissant des patterns fiables pour les tests.

## Patterns

### Pattern 1 : Monkeypatch avec lambda

```python
def test_something(tmp_path, monkeypatch):
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    # test code
```

### Pattern 2 : Patch de classe Path

```python
def test_something():
    with patch("pathlib.Path") as mock_path:
        fake_path = MagicMock()
        fake_path.exists.return_value = True
        fake_path.__truediv__ = MagicMock(return_value=fake_path)
        fake_path.parent.parent.__truediv__ = MagicMock(return_value=fake_path)
        mock_path.return_value = fake_path
        # test code
```

### Pattern 3 : Substitution de méthode d'instance

```python
def test_something(monkeypatch):
    original_exists = pathlib.Path.exists
    def fake_exists(self):
        if "toolchains.yaml" in str(self):
            return False
        return original_exists(self)
    monkeypatch.setattr("pathlib.Path.exists", fake_exists)
    # test code
```

## Anti-patterns

- ❌ `monkeypatch.setattr("Path.home", return_value=tmp_path)` → API incorrecte
- ❌ `patch("src.module.Path")` quand Path est importé localement dans la fonction
- ❌ Oublier de restaurer l'original après le test

## Checklist

- [ ] `Path.home()` mocké via `lambda`, pas `return_value=`
- [ ] Chemins relatifs convertis en absolus avant mock
- [ ] `__truediv__` chaîné pour `parent.parent / "config" / "toolchains.yaml"`

## Référence
- Incident : `ERR-MOCK-002` — monkeypatch.setattr avec return_value
- Module : `diagnostics.py::check_toolchains`
- Test : `tests/unit/test_diagnostics.py`
