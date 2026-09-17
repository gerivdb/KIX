"""Contrat de base pour BaseRunner KIX.

IntentHash: 0xPRD_MOC_VOLTX_PHASE3_RUNNERS_STANDARD_20260905
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

KIX_ROOT = Path(r"D:\DO\WEB\TOOLS\L2-PLATFORM\KIX")
if str(KIX_ROOT) not in sys.path:
    sys.path.insert(0, str(KIX_ROOT))

from src.kix.runner_base import BaseRunner, RunnerSpec


def test_runner_spec_creation() -> None:
    spec = RunnerSpec(
        name="test-runner",
        runner_type="python",
        port=8800,
        working_dir=KIX_ROOT / "runners" / "auto-index",
    )
    assert spec.name == "test-runner"
    assert spec.port == 8800
    assert spec.runner_type == "python"


def test_base_runner_abstract() -> None:
    """BaseRunner ne peut pas être instanciée directement."""
    spec = RunnerSpec(
        name="test",
        runner_type="python",
        port=8800,
        working_dir=KIX_ROOT,
    )
    with pytest.raises(TypeError):
        BaseRunner(spec)


def test_settings_module_exists() -> None:
    """Le module config.py existe et expose Settings."""
    from src.kix.config import Settings  # noqa: F401
