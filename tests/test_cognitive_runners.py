"""Tests for Cognitive Runners registry and CI pipeline."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from scripts.cognitive_runners import (
    COGNITIVE_RUNNERS,
    get_all_runners,
    get_runners_by_layer,
    get_existing_runners,
    get_layers,
    get_runners_ordered_by_layer,
    CognitiveRunner,
    LAYER_ORDER,
)


class TestCognitiveRunnersRegistry:
    """Tests for the cognitive runners registry."""

    def test_total_runners_count(self):
        """Should have exactly 17 cognitive runners."""
        assert len(COGNITIVE_RUNNERS) == 17

    def test_layers_present(self):
        """Should have all 4 cognitive layers."""
        layers = get_layers()
        assert "RLM" in layers
        assert "TLM" in layers
        assert "LLM" in layers
        assert "TEMPORAL" in layers
        assert len(layers) == 4

    def test_rlm_runners_count(self):
        """RLM layer should have 7 runners."""
        rlm = get_runners_by_layer("RLM")
        assert len(rlm) == 7
        names = {r.name for r in rlm}
        assert "RLM-SECURE" in names
        assert "RLM-DEPLOY" in names
        assert "RLM-GRAPH" in names
        assert "RLM-CONFIG" in names
        assert "RLM-INCIDENT" in names
        assert "RLM-RELEASE" in names
        assert "RLM-METRICS" in names

    def test_tlm_runners_count(self):
        """TLM layer should have 4 runners."""
        tlm = get_runners_by_layer("TLM")
        assert len(tlm) == 4

    def test_llm_runners_count(self):
        """LLM layer should have 4 runners."""
        llm = get_runners_by_layer("LLM")
        assert len(llm) == 4

    def test_temporal_runners_count(self):
        """TEMPORAL layer should have 2 runners."""
        temporal = get_runners_by_layer("TEMPORAL")
        assert len(temporal) == 2

    def test_runner_properties(self):
        """Each runner should have required properties."""
        for runner in COGNITIVE_RUNNERS:
            assert isinstance(runner.name, str)
            assert isinstance(runner.port, int)
            assert runner.port > 0
            assert runner.layer in ("RLM", "TLM", "LLM", "TEMPORAL")
            assert isinstance(runner.path_suffix, str)
            assert len(runner.path_suffix) > 0

    def test_unique_names(self):
        """All runner names should be unique."""
        names = [r.name for r in COGNITIVE_RUNNERS]
        assert len(names) == len(set(names))

    def test_unique_ports(self):
        """All runner ports should be unique."""
        ports = [r.port for r in COGNITIVE_RUNNERS]
        assert len(ports) == len(set(ports))

    def test_layer_order(self):
        """Layer order should be RLM -> TLM -> LLM -> TEMPORAL."""
        assert LAYER_ORDER == ("RLM", "TLM", "LLM", "TEMPORAL")

    def test_ordered_by_layer(self):
        """Runners ordered by layer should respect LAYER_ORDER."""
        ordered = get_runners_ordered_by_layer()
        assert len(ordered) == 17
        
        # Check first is RLM, last is TEMPORAL
        assert ordered[0].layer == "RLM"
        assert ordered[-1].layer == "TEMPORAL"
        
        # Check layer boundaries
        rlm_end = next(i for i, r in enumerate(ordered) if r.layer != "RLM")
        tlm_end = next(i for i, r in enumerate(ordered[rlm_end:], rlm_end) if r.layer != "TLM")
        llm_end = next(i for i, r in enumerate(ordered[tlm_end:], tlm_end) if r.layer != "LLM")
        
        assert rlm_end == 7      # 7 RLM runners
        assert tlm_end == 11     # 4 TLM runners (7+4)
        assert llm_end == 15     # 4 LLM runners (11+4)
        assert len(ordered) == 17  # 2 TEMPORAL runners


class TestRunnerCiPipeline:
    """Tests for the CI pipeline logic."""

    def test_calculate_optimal_workers_single_runner(self):
        """Should return 1 worker for single runner."""
        from scripts.runner_ci import calculate_optimal_workers
        assert calculate_optimal_workers(1) == 1

    def test_calculate_optimal_workers_many_runners_limited_by_cpu(self):
        """Should be limited by CPU cores."""
        from scripts.runner_ci import calculate_optimal_workers
        # Mock os.cpu_count to return 4
        with patch("os.cpu_count", return_value=4):
            # 10 runners, 4 cores -> max 3 workers (4-1)
            assert calculate_optimal_workers(10) == 3

    def test_calculate_optimal_workers_single_core(self):
        """Should handle single core machine."""
        from scripts.runner_ci import calculate_optimal_workers
        with patch("os.cpu_count", return_value=1):
            assert calculate_optimal_workers(5) == 1

    def test_wait_for_port_timeout(self):
        """wait_for_port should timeout for non-responsive port."""
        from scripts.runner_ci import wait_for_port
        # Port 1 is very unlikely to respond
        assert wait_for_port(1, timeout=0.5) is False


class TestCognitiveRunnerDataclass:
    """Tests for CognitiveRunner dataclass."""

    def test_rlm_secure_properties(self):
        """RLM-SECURE should have correct properties."""
        runner = next(r for r in COGNITIVE_RUNNERS if r.name == "RLM-SECURE")
        assert runner.port == 8797
        assert runner.layer == "RLM"
        assert runner.path_suffix == "RLM-SECURE"

    def test_dependencies_field(self):
        """Dependencies field should be tuple."""
        for runner in COGNITIVE_RUNNERS:
            assert isinstance(runner.dependencies, tuple)