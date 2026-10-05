"""KIX runner classifier using PIANO Base243 operator_T."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

PIANO_SRC = Path(r"D:\DO\WEB\TOOLS\L4-TOOLS\REPO-STANDARDS\PIANO\src")
if str(PIANO_SRC) not in sys.path:
    sys.path.insert(0, str(PIANO_SRC))

from operator_t import (  # type: ignore[import]
    operator_T,
    state_to_index,
    index_to_state,
)

LEVELS = ["invalide", "douteux", "valide"]


def _clamp_level(value: float, max_value: float = 4.0) -> int:
    return max(0, min(4, int(value / max_value)))


def _metrics_to_state(metrics: dict) -> tuple[str, str, str, str, str]:
    cpu = min(2, _clamp_level(metrics.get("cpu", 0)))
    memory = min(2, _clamp_level(metrics.get("memory", 0)))
    error_rate = min(2, _clamp_level(metrics.get("error_rate", 0) * 5))

    value = LEVELS[cpu]
    dynamique = LEVELS[memory]
    semantique = LEVELS[error_rate]
    intensite = "moyen"
    temporal = "en-cours"
    return value, dynamique, semantique, intensite, temporal


def _safe_state_to_index(state: tuple[str, str, str, str, str]) -> int:
    try:
        return state_to_index(state)
    except ValueError:
        return 242


def evaluate_runner_state(runner_id: str, metrics: dict) -> int:
    state = _metrics_to_state(metrics)
    transformed = operator_T(state)
    return _safe_state_to_index(transformed)


def evaluate_runners(runner_states: Iterable[tuple[str, dict]]) -> dict[str, int]:
    return {runner_id: evaluate_runner_state(runner_id, metrics) for runner_id, metrics in runner_states}
