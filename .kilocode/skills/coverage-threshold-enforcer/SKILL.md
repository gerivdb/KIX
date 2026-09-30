---
name: coverage-threshold-enforcer
description: Vérifie que chaque module atteint un seuil minimal de couverture avant de déclarer completed. Bloque les faux négatifs de coverage.
version: 1.0.0
intent_hash: 0xCOVERAGE_THRESHOLD_ENFORCER_20260930
---

# Coverage Threshold Enforcer

## Objectif
Garantir qu'aucun module n'est déclaré `completed` sans avoir atteint le seuil de couverture défini, éliminant les déclarations prématurées (`ERR-COV-001`).

## Usage

```python
import subprocess
import sys

def check_module_coverage(module_path: str, threshold: int = 100) -> dict:
    """Vérifie la couverture d'un module spécifique."""
    result = subprocess.run(
        [
            sys.executable, "-m", "pytest",
            f"--cov={module_path}",
            "--cov-report=term-missing",
            "-q"
        ],
        capture_output=True,
        text=True,
    )
    # Parser la sortie coverage
    for line in result.stdout.splitlines():
        if module_path in line:
            parts = line.split()
            cover = parts[-2].replace("%", "")
            return {"module": module_path, "coverage": int(cover), "passed": int(cover) >= threshold}
    return {"module": module_path, "coverage": 0, "passed": False}
```

## Seuils par défaut

| Type de module | Seuil |
|----------------|-------|
| Module critique (auth, bootstrap) | 100% |
| Module standard | 95% |
| Module en draft | 80% |

## Intégration PRD-MOC

```markdown
| Module | Action | Seuil | Statut |
|--------|--------|-------|--------|
| `src/auth.py` | Vérifier 100% | 100% | ✅ 100% |
| `src/diagnostics.py` | Compléter tests | 95% | ✅ 96% |
```

## Anti-patterns

- ❌ Déclarer `completed` sans vérifier la couverture
- ❌ Ignorer les lignes `__main__` triviales dans le calcul
- ❌ Utiliser `--cov=src` au lieu de `--cov=module` pour les vérifications individuelles

## Référence
- Incident : `ERR-COV-001` — diagnostics.py bloqué à 96% par lignes triviales
- PRD-MOC : `PRD-MOC-KIX-TEST-COVERAGE-100-20260929.md`
