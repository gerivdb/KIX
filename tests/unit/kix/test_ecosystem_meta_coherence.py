#!/usr/bin/env python3
r"""
Test EcosystemMetaCoherenceKix (PRD-MOC-KIX-ECOSYSTEM-META-COHERENCE-CONSUMER-20260928)
"""
import io
import sys

# ERR_030 FIX
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from kix.pipelines.ecosystem_meta_coherence import EcosystemMetaCoherenceKix


def test_verify_coherent():
    """verify returns COHERENT when all checks pass."""
    emc = EcosystemMetaCoherenceKix(context={
        "coherence_checks": [
            {"name": "registry_sync", "coherent": True},
            {"name": "port_consistency", "coherent": True},
        ]
    })
    result = emc.verify()
    assert result["status"] == "COHERENT"
    assert len(result["checks"]) == 2
    assert result["drifts"] == []


def test_verify_drift_detected():
    """verify returns DRIFT_DETECTED when any check fails."""
    emc = EcosystemMetaCoherenceKix(context={
        "coherence_checks": [
            {"name": "registry_sync", "coherent": True},
            {"name": "port_consistency", "coherent": False, "expected": 8800, "actual": 8801},
        ]
    })
    result = emc.verify()
    assert result["status"] == "DRIFT_DETECTED"
    assert len(result["drifts"]) == 1
    assert result["drifts"][0]["name"] == "port_consistency"


def test_verify_empty_checks():
    """verify returns COHERENT for empty checks list."""
    emc = EcosystemMetaCoherenceKix()
    result = emc.verify()
    assert result["status"] == "COHERENT"
    assert result["checks"] == []


def test_get_gaps_returns_drifts():
    """get_gaps returns drifts from verify."""
    emc = EcosystemMetaCoherenceKix(context={
        "coherence_checks": [
            {"name": "registry_sync", "coherent": False},
        ]
    })
    gaps = emc.get_gaps()
    assert len(gaps) == 1
    assert gaps[0]["name"] == "registry_sync"


def test_get_gaps_empty():
    """get_gaps returns empty list when coherent."""
    emc = EcosystemMetaCoherenceKix(context={
        "coherence_checks": [
            {"name": "registry_sync", "coherent": True},
        ]
    })
    gaps = emc.get_gaps()
    assert gaps == []


def test_verify_timestamp_utc():
    """verify includes ISO UTC timestamp."""
    emc = EcosystemMetaCoherenceKix()
    result = emc.verify()
    assert "timestamp" in result
    assert result["timestamp"].endswith("+00:00") or result["timestamp"].endswith("Z")
