"""
Tests d'intégration — Handler piano-inject KIX ⇄ ENV3.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

KIX = Path(__file__).resolve().parents[1]
HANDLER_PATH = KIX / "src" / "handlers" / "piano_inject.py"


def _import_handler():
    if str(KIX) not in sys.path:
        sys.path.insert(0, str(KIX))
    spec = importlib.util.spec_from_file_location("KIX.src.handlers.piano_inject", HANDLER_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["KIX.src.handlers.piano_inject"] = module
    spec.loader.exec_module(module)
    return module


def test_validate_perimeter_blocks_sot_references() -> None:
    module = _import_handler()
    with pytest.raises(PermissionError):
        module._validate_perimeter(module.PianoInjectRequest(trits="0,0,0,0,0", frequency="known_repositories.yaml"))


def test_load_runner_config_returns_piano_inject() -> None:
    module = _import_handler()
    config = module._load_runner_config()
    assert config["name"] == "piano-inject"
    assert config["telemetry_topic"] == "e2e.proof.bridge-env3.kix"


def test_run_piano_inject_succeeds() -> None:
    module = _import_handler()
    request = module.PianoInjectRequest(trits="0,0,0,0,0", frequency="base")
    result = module.run_piano_inject(request)
    assert result.status == "ok"
    assert result.exit_code == 0
    assert result.payload["intent_hash"] == request.intent_hash
    assert result.payload["execution_id"] == request.execution_id
    assert len(result.payload["trits"]) == 5
