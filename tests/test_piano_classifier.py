"""Tests for PIANO Base243 KIX runner classifier (Axe 1)."""
from __future__ import annotations

import pytest

from src.runners_classifier import (
    _clamp_level,
    _metrics_to_state,
    evaluate_runner_state,
    evaluate_runners,
)


class TestClampLevel:
    def test_zero_stays_zero(self):
        assert _clamp_level(0.0) == 0

    def test_negative_clamps_to_zero(self):
        assert _clamp_level(-10.0) == 0

    def test_over_max_clamps_to_four(self):
        assert _clamp_level(999.0) == 4

    def test_fractional_floor(self):
        assert _clamp_level(1.9) == 0
        assert _clamp_level(2.0) == 0
        assert _clamp_level(5.0) == 1


class TestMetricsToState:
    def test_default_metrics(self):
        state = _metrics_to_state({})
        assert len(state) == 5
        assert all(part in ["invalide", "douteux", "valide"] for part in state[:3])

    def test_high_metrics(self):
        state = _metrics_to_state({"cpu": 100.0, "memory": 100.0, "error_rate": 1.0})
        assert state == ("valide", "valide", "douteux", "moyen", "en-cours")

    def test_medium_metrics(self):
        state = _metrics_to_state({"cpu": 30.0, "memory": 30.0, "error_rate": 0.3})
        assert state == ("valide", "valide", "invalide", "moyen", "en-cours")


class TestEvaluateRunnerState:
    def test_returns_base243_index(self):
        result = evaluate_runner_state("runner-1", {"cpu": 100.0, "memory": 100.0, "error_rate": 1.0})
        assert 0 <= result <= 242

    def test_deterministic(self):
        result1 = evaluate_runner_state("runner-1", {"cpu": 100.0, "memory": 100.0, "error_rate": 1.0})
        result2 = evaluate_runner_state("runner-1", {"cpu": 100.0, "memory": 100.0, "error_rate": 1.0})
        assert result1 == result2


class TestEvaluateRunners:
    def test_batch_evaluation(self):
        runner_states = [
            ("runner-1", {"cpu": 100.0, "memory": 100.0, "error_rate": 1.0}),
            ("runner-2", {"cpu": 10.0, "memory": 10.0, "error_rate": 0.1}),
        ]
        result = evaluate_runners(runner_states)
        assert set(result.keys()) == {"runner-1", "runner-2"}
        assert all(0 <= value <= 242 for value in result.values())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
