#!/usr/bin/env python3
r"""
Test SafeActionGateKix (PRD-MOC-KIX-SAFE-ACTION-PATTERN-CONSUMER-20260928)
"""
import io
import sys

# ERR_030 FIX
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from kix.pipelines.safe_action_gate import SafeActionGateKix


def test_validate_with_met_preconditions():
    """validate returns True when all preconditions are met."""
    gate = SafeActionGateKix(context={
        "preconditions": [
            {"name": "dependency_check", "met": True},
            {"name": "config_check", "met": True},
        ]
    })
    assert gate.validate() is True


def test_validate_with_missing_preconditions():
    """validate returns False when any precondition is not met."""
    gate = SafeActionGateKix(context={
        "preconditions": [
            {"name": "dependency_check", "met": True},
            {"name": "config_check", "met": False},
        ]
    })
    assert gate.validate() is False


def test_validate_empty_preconditions():
    """validate returns False when preconditions list is empty."""
    gate = SafeActionGateKix()
    assert gate.validate() is False


def test_get_invariants_returns_list():
    """get_invariants returns invariants from context."""
    gate = SafeActionGateKix(context={
        "invariants": [
            {"name": "no_force_push"},
            {"name": "backup_before_mutation"},
        ]
    })
    invariants = gate.get_invariants()
    assert len(invariants) == 2
    assert invariants[0]["name"] == "no_force_push"


def test_get_proof_returns_structure():
    """get_proof returns expected proof structure."""
    gate = SafeActionGateKix(context={
        "preconditions": [{"met": True}],
        "invariants": [{"name": "inv1"}],
    })
    proof = gate.get_proof()
    assert proof["design"] == "safe-action-pattern"
    assert "validated" in proof
    assert "invariants" in proof
    assert "timestamp" in proof


def test_get_proof_validated_false_when_preconditions_missing():
    """get_proof validated is False when preconditions missing."""
    gate = SafeActionGateKix()
    proof = gate.get_proof()
    assert proof["validated"] is False
