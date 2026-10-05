"""
Handler KIX pour l'injection d'état piano (5 trits) vers TRIX via clusterwave timing.

Aligné sur PRD-MOC-KIX-ENV3-BRIDGE-20261004 :
- Runner : piano-inject
- Topic WAZAA : e2e.proof.bridge-env3.kix
- Topologie : ENV3 -> GATEWAY-MANAGER -> KIX -> TRIX
"""
from __future__ import annotations

import json
import logging
import os
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import yaml

RUNNERS_YAML = Path(__file__).resolve().parents[2] / "config" / "runners.yaml"
RUNNER_NAME = "piano-inject"
TELEMETRY_TOPIC = "e2e.proof.bridge-env3.kix"
ALLOWED_STRATES = ["L0", "L1", "L2", "L3", "L4", "L5", "L6"]
FORBIDDEN_PATHS = [
    "known_repositories.yaml",
    "AGENT_RAM.yaml",
    "BRIDGES.yaml",
]
WAL_PATH = Path(__file__).resolve().parents[2] / "logs" / "bridge_wal.jsonl"


@dataclass
class PianoInjectRequest:
    trits: str
    frequency: str
    intent_hash: Optional[str] = None
    execution_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.execution_id is None:
            self.execution_id = str(uuid.uuid4())
        if self.intent_hash is None:
            self.intent_hash = f"0xINTENT_{RUNNER_NAME.upper()}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"


@dataclass
class PianoInjectResult:
    status: str
    duration_ms: int
    exit_code: int
    payload: dict
    error: Optional[str] = None


def _load_runner_config() -> dict:
    if not RUNNERS_YAML.exists():
        raise FileNotFoundError(f"Runners config not found: {RUNNERS_YAML}")
    with RUNNERS_YAML.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    runners = {r.get("name"): r for r in data.get("runners", [])}
    if RUNNER_NAME not in runners:
        raise ValueError(f"Runner '{RUNNER_NAME}' not registered in {RUNNERS_YAML}")
    return runners[RUNNER_NAME]


def _validate_perimeter(request: PianoInjectRequest) -> None:
    """G-PERIMETER : valider les bornes et interdire l'accès à la SOT."""
    for forbidden in FORBIDDEN_PATHS:
        if forbidden in request.trits or forbidden in request.frequency:
            raise PermissionError(f"G-PERIMETER violation: forbidden path '{forbidden}' referenced")


def _wal_append(record: dict) -> None:
    WAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with WAL_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _emit_waazaa(event: str, payload: dict) -> None:
    """Émettre un événement WAZAA (stub télémetrie)."""
    record = {
        "topic": TELEMETRY_TOPIC,
        "event": event,
        "payload": payload,
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
    }
    logging.debug("WAZAA emit: %s", json.dumps(record, ensure_ascii=False))
    _wal_append(record)


def _build_trix_payload(request: PianoInjectRequest) -> dict:
    """Construire le payload TRIX piano-inject."""
    trits = [int(x.strip()) for x in request.trits.split(",")]
    if len(trits) != 5:
        raise ValueError("piano-inject requires exactly 5 trits")
    return {
        "intent_hash": request.intent_hash,
        "execution_id": request.execution_id,
        "trits": trits,
        "frequency": request.frequency,
        "clusterwave_timing": True,
    }


def run_piano_inject(request: PianoInjectRequest) -> PianoInjectResult:
    """Exécuter le handler piano-inject."""
    start = time.time()
    try:
        _validate_perimeter(request)
        runner = _load_runner_config()
        payload = _build_trix_payload(request)
        _emit_waazaa("runner_started", {
            "intent_hash": request.intent_hash,
            "runner_name": RUNNER_NAME,
            "execution_id": request.execution_id,
        })
        duration_ms = int((time.time() - start) * 1000)
        _emit_waazaa("runner_completed", {
            "intent_hash": request.intent_hash,
            "execution_id": request.execution_id,
            "exit_code": 0,
            "duration_ms": duration_ms,
        })
        return PianoInjectResult(
            status="ok",
            duration_ms=duration_ms,
            exit_code=0,
            payload=payload,
        )
    except Exception as exc:  # noqa: BLE001
        duration_ms = int((time.time() - start) * 1000)
        _emit_waazaa("runner_failed", {
            "intent_hash": request.intent_hash,
            "execution_id": request.execution_id,
            "error": str(exc),
            "retry_count": 0,
            "fallback_triggered": False,
        })
        return PianoInjectResult(
            status="error",
            duration_ms=duration_ms,
            exit_code=1,
            payload={},
            error=str(exc),
        )
