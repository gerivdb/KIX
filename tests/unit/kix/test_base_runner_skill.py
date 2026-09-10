#!/usr/bin/env python3
r"""
Test BaseRunner + BaseSkill + SkillRunner (P1-T09)
"""
import io
import sys
import tempfile
from pathlib import Path

# ERR_030 FIX
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

_shared_path = str(Path(__file__).resolve().parent.parent.parent.parent / "kix" / "libs" / "shared-clients")
sys.path.insert(0, _shared_path)

from base_runner import BaseRunner
from base_skill import BaseSkill
from skill_runner import SkillRunner


def test_baseskill_concrete_methods():
    """BaseSkill: narrate() and complete() are concrete."""
    
    class TestSkill(BaseSkill):
        skill_id = "test-skill"
        skill_name = "TestSkill"
        
        def prepare(self) -> dict:
            return {"context": "ready"}
        
        def analyze(self) -> dict:
            return {"result": "success", "value": 42}
    
    skill = TestSkill(context={"test": True})
    
    # narrate is concrete
    narrative = skill.narrate({"result": "success"})
    assert "TestSkill" in narrative
    assert "result" in narrative
    
    # complete is concrete (runs full pipeline)
    full_narrative = skill.complete()
    assert "Rapport" in full_narrative
    assert "success" in full_narrative


def test_baseskill_requires_abstract_methods():
    """BaseSkill: subclass must implement prepare() and analyze()."""
    try:
        class BadSkill(BaseSkill):
            pass
        
        BadSkill()
        assert False, "Should have raised TypeError for abstract methods"
    except TypeError:
        pass


def test_baserunner_health_structure():
    """BaseRunner: health() returns expected structure."""
    
    class TestRunner(BaseRunner):
        runner_name = "test-runner"
        
        def run(self):
            pass
    
    with tempfile.TemporaryDirectory() as tmpdir:
        runner = TestRunner(config={"vault_path": tmpdir, "kgl_host": "local"})
        
        # Without start(), start_time is None
        health = runner.health()
        assert health["status"] == "healthy"
        assert health["service"] == "test-runner"
        
        # Check required fields
        assert "uptime_seconds" in health
        assert "events_processed" in health
        assert "errors" in health


def test_baserunner_metrics_structure():
    """BaseRunner: metrics() returns Prometheus-style dict."""
    
    class TestRunner(BaseRunner):
        runner_name = "metrics-test"
        
        def run(self):
            pass
    
    with tempfile.TemporaryDirectory() as tmpdir:
        runner = TestRunner(config={"vault_path": tmpdir})
        metrics = runner.metrics()
        
        assert "metrics-test_events_total" in metrics
        assert "metrics-test_uptime_seconds" in metrics


def test_skillrunner_loads_skill():
    """SkillRunner: loads skill from file path."""
    
    # Create a test skill file
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_file = Path(tmpdir) / "test_skill.py"
        skill_file.write_text('''
import sys
sys.path.insert(0, "D:/DO/WEB/TOOLS/L0-CANON/GOVERNANCE-HUB/kix/libs/shared-clients")
from base_skill import BaseSkill

class TestSkill(BaseSkill):
    skill_id = "test"
    skill_name = "Test"
    def prepare(self):
        return {}
    def analyze(self):
        return {"result": "ok"}

SKILL = TestSkill
''', encoding="utf-8")
        
        runner = SkillRunner(skill_path=str(skill_file), config={"vault_path": tmpdir})
        assert runner.skill is not None, "Skill should be loaded"


# Test BaseRunner without Flask (to avoid server)
def test_baserunner_start_stop():
    """BaseRunner: start/stop cycles."""
    
    class TestRunner(BaseRunner):
        runner_name = "lifecycle-test"
        def run(self):
            pass
    
    with tempfile.TemporaryDirectory() as tmpdir:
        runner = TestRunner(config={"vault_path": tmpdir})
        runner.start()
        assert runner._running == True
        assert runner._start_time is not None
        runner.stop()
        assert runner._running == False


if __name__ == "__main__":
    tests = [
        test_baseskill_concrete_methods,
        test_baseskill_requires_abstract_methods,
        test_baserunner_health_structure,
        test_baserunner_metrics_structure,
        test_skillrunner_loads_skill,
        test_baserunner_start_stop,
    ]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  [OK] {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"  [KO] {test.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
