"""Validation basique du squelette BaseRunner KIX (hors pytest)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

KIX_ROOT = Path(r"D:\DO\WEB\TOOLS\L2-PLATFORM\KIX")
sys.path.insert(0, str(KIX_ROOT))

from src.kix.runner_base import BaseRunner, RunnerSpec
from src.kix.config import Settings


def test_runner_spec_creation() -> bool:
    spec = RunnerSpec(
        name="test-runner",
        runner_type="python",
        port=8800,
        working_dir=KIX_ROOT / "runners" / "auto-index",
    )
    assert spec.name == "test-runner"
    assert spec.port == 8800
    assert spec.runner_type == "python"
    return True


def test_base_runner_abstract() -> bool:
    spec = RunnerSpec(
        name="test",
        runner_type="python",
        port=8800,
        working_dir=KIX_ROOT,
    )
    runner = BaseRunner(spec)
    assert runner.spec.name == "test"
    with pytest.raises(NotImplementedError):
        runner.start()
    return True


def test_settings_module_exists() -> bool:
    settings = Settings()
    assert settings.log_level == "INFO"
    return True


if __name__ == "__main__":
    results = [
        test_runner_spec_creation(),
        test_base_runner_abstract(),
        test_settings_module_exists(),
    ]
    print(f"BaseRunner skeleton validation: {sum(results)}/{len(results)} passed")
    sys.exit(0 if all(results) else 1)
