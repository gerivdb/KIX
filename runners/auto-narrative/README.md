# Auto-Narrative Runner

Runner KIX pour la boucle auto-narrative BT-1.

## Usage

```python
from runners.auto_narrative.main import AutoNarrativeRunner

runner = AutoNarrativeRunner()
runner.start()
```

## Configuration

- Port: 8795
- Max cycles: 3
- Delta threshold: 0.05

## Proof-of-Life

- [x] 2026-09-18T00:14:00+02:00 — Runner squelette créé, hérite BaseRunner, import OK
