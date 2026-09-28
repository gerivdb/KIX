#!/usr/bin/env python3
r"""
Test TalexFrictionAnalyzerKix (PRD-MOC-KIX-TALEX-FRICTION-ANALYZER-CONSUMER-20260928)
"""
import io
import sys

# ERR_030 FIX
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from kix.pipelines.talex_friction_analyzer import TalexFrictionAnalyzerKix


def test_detect_frictions():
    """detect_frictions returns frictions from context."""
    analyzer = TalexFrictionAnalyzerKix(context={
        "frictions": [
            {"code": "ERR-001", "message": "test"},
        ]
    })
    frictions = analyzer.detect_frictions()
    assert len(frictions) == 1
    assert frictions[0]["code"] == "ERR-001"


def test_analyze_root_causes():
    """analyze_root_causes returns root causes from context."""
    analyzer = TalexFrictionAnalyzerKix(context={
        "root_causes": [
            "cause 1",
            "cause 2",
        ]
    })
    causes = analyzer.analyze_root_causes()
    assert len(causes) == 2
    assert "cause 1" in causes


def test_classify_known_error():
    """Classification identifies known ERR codes."""
    analyzer = TalexFrictionAnalyzerKix()
    classification = analyzer.classify({
        "code": "ERR-001",
        "category": "runtime",
        "severity": "high",
        "structural": True,
        "causal": True,
    })
    assert classification["known"] is True
    assert classification["label"] == "Double-bind port Windows"
    assert classification["structural"] is True


def test_classify_unknown_error():
    """Classification marks unknown codes."""
    analyzer = TalexFrictionAnalyzerKix()
    classification = analyzer.classify({
        "code": "ERR-999",
        "category": "unknown",
        "severity": "low",
        "structural": False,
        "causal": False,
    })
    assert classification["known"] is False
    assert classification["label"] == "Inconnu"


def test_propose_correction_hook_empty_graph():
    """propose_correction returns atomic fix for ERR-KIX-HOOK-EMPTY-GRAPH."""
    analyzer = TalexFrictionAnalyzerKix()
    correction = analyzer.propose_correction({
        "code": "ERR-KIX-HOOK-EMPTY-GRAPH",
    })
    assert correction["atomic"] is True
    assert "validate_designs" in correction["file"]


def test_propose_correction_unknown():
    """propose_correction returns manual_review for unknown codes."""
    analyzer = TalexFrictionAnalyzerKix()
    correction = analyzer.propose_correction({
        "code": "ERR-UNKNOWN",
    })
    assert correction["atomic"] is False
    assert correction["action"] == "manual_review"


def test_analyze_summary_counts():
    """analyze returns correct summary counts."""
    analyzer = TalexFrictionAnalyzerKix(context={
        "frictions": [
            {"code": "ERR-001", "category": "runtime", "severity": "high", "structural": True, "causal": True},
            {"code": "ERR-999", "category": "unknown", "severity": "low", "structural": False, "causal": False},
        ]
    })
    result = analyzer.analyze()
    summary = result["summary"]
    assert summary["total"] == 2
    assert summary["known"] == 1
    assert summary["unknown"] == 1
    assert summary["structural"] == 1
    assert summary["causal"] == 1


def test_analyze_returns_completed_status():
    """analyze returns COMPLETED status."""
    analyzer = TalexFrictionAnalyzerKix(context={"frictions": []})
    result = analyzer.analyze()
    assert result["status"] == "COMPLETED"
    assert "timestamp" in result
    assert "design" in result
