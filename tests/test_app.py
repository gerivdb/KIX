"""Tests for KIX orchestrator."""

from pathlib import Path

from src.runner_state import RunnerStateStore
from src.app import _load_known_repositories


def test_runner_state_roundtrip() -> None:
    db_path = Path(__file__).resolve().parent.parent / "data" / "test.sqlite"
    store = RunnerStateStore(str(db_path))
    store.upsert("RLM-GRAPH", "running", 1234, "2026-07-27T22:00:00+00:00", "2026-07-27T22:01:00+00:00")
    record = store.get("RLM-GRAPH")
    assert record is not None
    assert record.status == "running"
    assert record.pid == 1234
    all_records = store.list_all()
    assert "RLM-GRAPH" in all_records


def test_known_repositories_loader() -> None:
    runners = _load_known_repositories()
    assert len(runners) > 0
    names = {r.name for r in runners}
    assert "KIX" in names
    assert "RLM-GRAPH" in names
