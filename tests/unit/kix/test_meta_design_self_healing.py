#!/usr/bin/env python3
r"""
Test MetaDesignSelfHealingKix (PRD-MOC-KIX-META-DESIGN-SELF-HEALING-CONSUMER-20260928)
"""
import io
import sys

# ERR_030 FIX
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from kix.pipelines.meta_design_self_healing import MetaDesignSelfHealingKix


def test_scan_returns_gaps():
    """scan returns gaps from context."""
    healing = MetaDesignSelfHealingKix(context={
        "gaps": [
            {"id": "gap-1", "file": "src/app.py"},
        ]
    })
    gaps = healing.scan()
    assert len(gaps) == 1
    assert gaps[0]["id"] == "gap-1"


def test_propose_patches_returns_patches():
    """propose_patches returns patches for each gap."""
    healing = MetaDesignSelfHealingKix(context={
        "gaps": [
            {"id": "gap-1", "suggested_action": "add_field", "atomic": True, "file": "src/app.py"},
        ]
    })
    patches = healing.propose_patches()
    assert len(patches) == 1
    assert patches[0]["patch"]["action"] == "add_field"
    assert patches[0]["patch"]["atomic"] is True


def test_analyze_returns_completed_status():
    """analyze returns COMPLETED status."""
    healing = MetaDesignSelfHealingKix(context={"gaps": []})
    result = healing.analyze()
    assert result["status"] == "COMPLETED"
    assert "timestamp" in result
    assert "design" in result


def test_analyze_summary_counts():
    """analyze returns correct summary counts."""
    healing = MetaDesignSelfHealingKix(context={
        "gaps": [
            {"id": "gap-1", "suggested_action": "add_field", "atomic": True},
            {"id": "gap-2", "suggested_action": "manual_review", "atomic": False},
        ]
    })
    result = healing.analyze()
    assert result["summary"]["gaps"] == 2
    assert result["summary"]["patches"] == 2


def test_scan_empty_context():
    """scan returns empty list when no gaps."""
    healing = MetaDesignSelfHealingKix()
    gaps = healing.scan()
    assert gaps == []


def test_propose_patches_empty_context():
    """propose_patches returns empty list when no gaps."""
    healing = MetaDesignSelfHealingKix()
    patches = healing.propose_patches()
    assert patches == []
