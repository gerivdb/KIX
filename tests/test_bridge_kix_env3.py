"""
Tests for KIX ⇄ ENV3 bridge (PRD-MOC-KIX-ENV3-BRIDGE-20261004).
"""
import pytest
import os
import yaml

KIX_RUNNERS_YAML = "D:/DO/WEB/TOOLS/L2-PLATFORM/KIX/config/runners.yaml"
WAZAA_TOPICS_YAML = "D:/DO/WEB/TOOLS/L4-TOOLS/WAZAA/topics.yaml"


class TestKixEnv3Bridge:
    def test_piano_inject_runner_registered(self):
        """Runner piano-inject must be present in KIX runners.yaml."""
        with open(KIX_RUNNERS_YAML, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        runner_names = [r.get("name") for r in data.get("runners", [])]
        assert "piano-inject" in runner_names

    def test_piano_inject_telemetry_topic(self):
        """Runner piano-inject must reference WAZAA telemetry topic."""
        with open(KIX_RUNNERS_YAML, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        runners = {r.get("name"): r for r in data.get("runners", [])}
        piano = runners.get("piano-inject")
        assert piano is not None
        assert piano.get("telemetry_topic") == "e2e.proof.bridge-env3.kix"

    def test_waazaa_bridge_env3_topic_registered(self):
        """WAZAA must declare e2e.proof.bridge-env3.kix topic."""
        with open(WAZAA_TOPICS_YAML, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        topic_names = list(data.get("topics", {}).keys())
        assert "e2e.proof.bridge-env3.kix" in topic_names

    def test_waazaa_gateway_proof_topic_registered(self):
        """WAZAA must declare e2e.proof.bridge-env3.gateway topic."""
        with open(WAZAA_TOPICS_YAML, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        topic_names = list(data.get("topics", {}).keys())
        assert "e2e.proof.bridge-env3.gateway" in topic_names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
