#!/usr/bin/env python3
r"""
Test ArtifactLayersKix (PRD-MOC-KIX-ARTIFACT-LAYERS-DESIGN-CONSUMER-20260928)
"""
import io
import sys

# ERR_030 FIX
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from kix.pipelines.artifact_layers import ArtifactLayersKix


def test_validate_valid_layers():
    """validate returns VALID when all layers are valid."""
    layers = ArtifactLayersKix(context={
        "artifacts": [
            {"name": "core_module", "layer": "core"},
            {"name": "adapter", "layer": "adapter"},
            {"name": "ui", "layer": "presentation"},
        ]
    })
    result = layers.validate()
    assert result["status"] == "VALID"
    assert len(result["results"]) == 3


def test_validate_invalid_layers():
    """validate returns INVALID when a layer is invalid."""
    layers = ArtifactLayersKix(context={
        "artifacts": [
            {"name": "core_module", "layer": "core"},
            {"name": "invalid", "layer": "invalid"},
        ]
    })
    result = layers.validate()
    assert result["status"] == "INVALID"
    assert len(result["results"]) == 2


def test_validate_empty_artifacts():
    """validate returns VALID for empty artifacts list."""
    layers = ArtifactLayersKix()
    result = layers.validate()
    assert result["status"] == "VALID"
    assert result["results"] == []


def test_get_violations_returns_invalid():
    """get_violations returns only invalid artifacts."""
    layers = ArtifactLayersKix(context={
        "artifacts": [
            {"name": "core_module", "layer": "core"},
            {"name": "invalid", "layer": "invalid"},
        ]
    })
    violations = layers.get_violations()
    assert len(violations) == 1
    assert violations[0]["name"] == "invalid"


def test_get_violations_empty():
    """get_violations returns empty list when all layers are valid."""
    layers = ArtifactLayersKix(context={
        "artifacts": [
            {"name": "core_module", "layer": "core"},
        ]
    })
    violations = layers.get_violations()
    assert violations == []


def test_validate_timestamp_utc():
    """validate includes ISO UTC timestamp."""
    layers = ArtifactLayersKix()
    result = layers.validate()
    assert "timestamp" in result
    assert result["timestamp"].endswith("+00:00") or result["timestamp"].endswith("Z")
