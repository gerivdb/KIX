"""
Émetteur WAZAA pour KIX ⇄ ENV3.

Aligné sur PRD-MOC-KIX-ENV3-BRIDGE-20261004 :
- Topics : e2e.proof.bridge-env3.kix / e2e.proof.bridge-env3.gateway
- Mode : stub télémetrie + WAL local (prod : remplacement par client WAZAA réel)
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

WAL_PATH = Path(__file__).resolve().parents[2] / "logs" / "bridge_wal.jsonl"
TOPICS = [
    "e2e.proof.bridge-env3.kix",
    "e2e.proof.bridge-env3.gateway",
]


def _wal_append(record: Dict[str, Any]) -> None:
    WAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with WAL_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def emit(topic: str, event: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Émettre un événement WAZAA."""
    if topic not in TOPICS:
        raise ValueError(f"WAZAA topic non autorisé: {topic}")
    record = {
        "topic": topic,
        "event": event,
        "payload": payload,
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
    }
    logging.debug("WAZAA emit: %s", json.dumps(record, ensure_ascii=False))
    _wal_append(record)
    return record


def emit_runner_started(intent_hash: str, execution_id: str, runner_name: str = "piano-inject") -> Dict[str, Any]:
    return emit(
        topic="e2e.proof.bridge-env3.kix",
        event="runner_started",
        payload={
            "intent_hash": intent_hash,
            "execution_id": execution_id,
            "runner_name": runner_name,
        },
    )


def emit_runner_completed(intent_hash: str, execution_id: str, exit_code: int, duration_ms: int) -> Dict[str, Any]:
    return emit(
        topic="e2e.proof.bridge-env3.kix",
        event="runner_completed",
        payload={
            "intent_hash": intent_hash,
            "execution_id": execution_id,
            "exit_code": exit_code,
            "duration_ms": duration_ms,
        },
    )


def emit_runner_failed(intent_hash: str, execution_id: str, error: str, retry_count: int, fallback_triggered: bool) -> Dict[str, Any]:
    return emit(
        topic="e2e.proof.bridge-env3.kix",
        event="runner_failed",
        payload={
            "intent_hash": intent_hash,
            "execution_id": execution_id,
            "error": error,
            "retry_count": retry_count,
            "fallback_triggered": fallback_triggered,
        },
    )
