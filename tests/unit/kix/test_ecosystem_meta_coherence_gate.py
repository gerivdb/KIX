#!/usr/bin/env python3
r"""
Test EcosystemMetaCoherenceGateKix (PRD-MOC-KIX-ECOSYSTEM-META-COHERENCE-GATE-CONSUMER-20260928)
"""
import io
import sys

# ERR_030 FIX
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from kix.pipelines.ecosystem_meta_coherence_gate import EcosystemMetaCoherenceGateKix


def test_verify_pass():
    """verify returns PASS when all invariants are valid."""
    gate = EcosystemMetaCoherenceGateKix(context={
        "invariants": [
            {"name": "registry_consistency", "valid": True},
            {"name": "port_consistency", "valid": True},
        ]
    })
    result = gate.verify()
    assert result["status"] == "PASS"
    assert result["violations"] == []


def test_verify_fail():
    """verify returns FAIL when any invariant is invalid."""
    gate = EcosystemMetaCoherenceGateKix(context={
        "invariants": [
            {"name": "registry_consistency", "valid": True},
            {"name": "port_consistency", "valid": False, "expected": 8800, "actual": 8801},
        ]
    })
    result = gate.verify()
    assert result["status"] == "FAIL"
    assert len(result["violations"]) == 1
    assert result["violations"][0]["name"] == "port_consistency"


def test_verify_empty_invariants():
    """verify returns PASS for empty invariants list."""
    gate = EcosystemMetaCoherenceGateKix()
    result = gate.verify()
    assert result["status"] == "PASS"
    assert result["violations"] == []


def test_get_violations_returns_violations():
    """get_violations returns violations from verify."""
    gate = EcosystemMetaCoherenceGateKix(context={
        "invariants": [
            {"name": "registry_consistency", "valid": False},
        ]
    })
    violations = gate.get_violations()
    assert len(violations) == 1
    assert violations[0]["name"] == "registry_consistency"


def test_get_violations_empty():
    """get_violations returns empty list when all invariants are valid."""
    gate = EcosystemMetaCoherenceGateKix(context={
        "invariants": [
            {"name": "registry_consistency", "valid": True},
        ]
    })
    violations = gate.get_violations()
    assert violations == []


def test_verify_timestamp_utc():
    """verify includes ISO UTC timestamp."""
    gate = EcosystemMetaCoherenceGateKix()
    result = gate.verify()
    assert "timestamp" in result
    assert result["timestamp"].endswith("+00:00") or result["timestamp"].endswith("Z")
