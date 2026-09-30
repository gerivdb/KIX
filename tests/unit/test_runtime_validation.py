"""Tests for src/kix/runtime/validation.py."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.kix.runtime.validation import ValidationResult, validate_kg_l_runtime


class TestValidationResult:
    def test_default_issues_empty(self):
        result = ValidationResult(ok=True)
        assert result.issues == []

    def test_custom_issues(self):
        result = ValidationResult(ok=False, issues=["missing graph"])
        assert result.issues == ["missing graph"]


class TestValidateKgLRuntime:
    def test_missing_graph(self, tmp_path):
        graph_path = tmp_path / "missing_graph.json"
        registry_path = tmp_path / "registry.yaml"
        registry_path.write_text("repos: []")
        result = validate_kg_l_runtime(graph_path, registry_path)
        assert result.ok is False
        assert any("missing graph" in issue for issue in result.issues)

    def test_missing_registry(self, tmp_path):
        graph_path = tmp_path / "graph.json"
        graph_path.write_text(json.dumps({"nodes": []}))
        registry_path = tmp_path / "missing_registry.yaml"
        result = validate_kg_l_runtime(graph_path, registry_path)
        assert result.ok is False
        assert any("missing registry" in issue for issue in result.issues)

    def test_graph_load_failed(self, tmp_path):
        graph_path = tmp_path / "graph.json"
        graph_path.write_text("not-json")
        registry_path = tmp_path / "registry.yaml"
        registry_path.write_text("repos: []")
        result = validate_kg_l_runtime(graph_path, registry_path)
        assert result.ok is False
        assert any("graph load failed" in issue for issue in result.issues)

    def test_graph_empty(self, tmp_path):
        graph_path = tmp_path / "graph.json"
        graph_path.write_text(json.dumps({"nodes": []}))
        registry_path = tmp_path / "registry.yaml"
        registry_path.write_text("repos: []")
        result = validate_kg_l_runtime(graph_path, registry_path)
        assert result.ok is False
        assert any("graph empty" in issue for issue in result.issues)

    def test_valid_graph(self, tmp_path):
        graph = {
            "nodes": [
                {"id": "n1", "name": "A", "layer": "L1", "status": "ACTIVE", "entity_type": "REPO", "local_path": "/x", "remote": "r"},
                {"id": "n2", "name": "B", "layer": "L1", "status": "ACTIVE", "entity_type": "REPO", "local_path": "/y", "remote": "r"},
            ]
        }
        graph_path = tmp_path / "graph.json"
        graph_path.write_text(json.dumps(graph))
        registry_path = tmp_path / "registry.yaml"
        registry_path.write_text("repos: []")
        result = validate_kg_l_runtime(graph_path, registry_path)
        assert result.ok is True
        assert result.issues == []

    def test_node_missing_fields(self, tmp_path):
        graph = {
            "nodes": [
                {"id": "n1", "name": "A", "layer": "L1", "status": "ACTIVE", "entity_type": "REPO", "local_path": "/x", "remote": "r"},
                {"id": "n2", "name": "B", "layer": "L1", "status": "ACTIVE", "entity_type": "REPO", "local_path": "/y"},
            ]
        }
        graph_path = tmp_path / "graph.json"
        graph_path.write_text(json.dumps(graph))
        registry_path = tmp_path / "registry.yaml"
        registry_path.write_text("repos: []")
        result = validate_kg_l_runtime(graph_path, registry_path)
        assert result.ok is False
        assert any("missing=" in issue for issue in result.issues)

    def test_node_not_dict(self, tmp_path):
        graph = {
            "nodes": [
                "not-a-dict",
            ]
        }
        graph_path = tmp_path / "graph.json"
        graph_path.write_text(json.dumps(graph))
        registry_path = tmp_path / "registry.yaml"
        registry_path.write_text("repos: []")
        result = validate_kg_l_runtime(graph_path, registry_path)
        assert result.ok is False
        assert any("node is not dict" in issue for issue in result.issues)

    def test_node_skipped_without_local_path(self, tmp_path):
        graph = {
            "nodes": [
                {"id": "n1", "name": "A", "layer": "L1", "status": "ACTIVE", "entity_type": "REPO", "remote": "r"},
            ]
        }
        graph_path = tmp_path / "graph.json"
        graph_path.write_text(json.dumps(graph))
        registry_path = tmp_path / "registry.yaml"
        registry_path.write_text("repos: []")
        result = validate_kg_l_runtime(graph_path, registry_path)
        assert result.ok is True

    def test_node_skipped_when_not_active_repo(self, tmp_path):
        graph = {
            "nodes": [
                {"id": "n1", "name": "A", "layer": "L1", "status": "DORMANT", "entity_type": "REPO", "local_path": "/x", "remote": "r"},
            ]
        }
        graph_path = tmp_path / "graph.json"
        graph_path.write_text(json.dumps(graph))
        registry_path = tmp_path / "registry.yaml"
        registry_path.write_text("repos: []")
        result = validate_kg_l_runtime(graph_path, registry_path)
        assert result.ok is True
