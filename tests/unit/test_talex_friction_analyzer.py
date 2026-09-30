"""Tests for src/kix/pipelines/talex_friction_analyzer.py."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.kix.pipelines.talex_friction_analyzer import TalexFrictionAnalyzerKix, analyze_friction


class TestTalexFrictionAnalyzerKix:
    def test_detect_frictions_empty(self):
        analyzer = TalexFrictionAnalyzerKix()
        result = analyzer.detect_frictions()
        assert result == []

    def test_detect_frictions_with_context(self):
        analyzer = TalexFrictionAnalyzerKix()
        context = {"frictions": [{"code": "ERR-001", "severity": "high"}]}
        result = analyzer.detect_frictions(context)
        assert len(result) == 1
        assert result[0]["code"] == "ERR-001"

    def test_analyze_root_causes_empty(self):
        analyzer = TalexFrictionAnalyzerKix()
        result = analyzer.analyze_root_causes()
        assert result == []

    def test_analyze_root_causes_with_context(self):
        analyzer = TalexFrictionAnalyzerKix()
        context = {"root_causes": [{"cause": "port conflict"}]}
        result = analyzer.analyze_root_causes(context)
        assert len(result) == 1

    def test_classify_known_code(self):
        analyzer = TalexFrictionAnalyzerKix()
        friction = {"code": "ERR-001", "severity": "high"}
        result = analyzer.classify(friction)
        assert result["known"] is True
        assert result["label"] == "Double-bind port Windows"

    def test_classify_unknown_code(self):
        analyzer = TalexFrictionAnalyzerKix()
        friction = {"code": "ERR-999", "severity": "high"}
        result = analyzer.classify(friction)
        assert result["known"] is False
        assert result["label"] == "Inconnu"

    def test_propose_correction_err_kix_hook_empty_graph(self):
        analyzer = TalexFrictionAnalyzerKix()
        friction = {"code": "ERR-KIX-HOOK-EMPTY-GRAPH"}
        result = analyzer.propose_correction(friction)
        assert result["action"] == "fix_registry_lookup"
        assert result["atomic"] is True

    def test_propose_correction_err_kix_merge_conflict(self):
        analyzer = TalexFrictionAnalyzerKix()
        friction = {"code": "ERR-KIX-MERGE-CONFLICT-INTERCEPTION-LOG"}
        result = analyzer.propose_correction(friction)
        assert result["action"] == "resolve_in_favor_of_main"
        assert result["atomic"] is True

    def test_propose_correction_err_kix_hook_cyclic_regen(self):
        analyzer = TalexFrictionAnalyzerKix()
        friction = {"code": "ERR-KIX-HOOK-CYCLIC-REGEN"}
        result = analyzer.propose_correction(friction)
        assert result["action"] == "add_dirty_check"
        assert result["atomic"] is True

    def test_propose_correction_err_kix_powershell_invoke_rest(self):
        analyzer = TalexFrictionAnalyzerKix()
        friction = {"code": "ERR-KIX-POWERSHELL-INVOKE-REST"}
        result = analyzer.propose_correction(friction)
        assert result["action"] == "use_python_requests"
        assert result["atomic"] is True

    def test_propose_correction_err_kix_uncommitted_batch_commit(self):
        analyzer = TalexFrictionAnalyzerKix()
        friction = {"code": "ERR-KIX-UNCOMMITTED-BATCH-COMMIT"}
        result = analyzer.propose_correction(friction)
        assert result["action"] == "split_into_atomic_commits"
        assert result["atomic"] is True

    def test_propose_correction_err_kix_git_merge_local_changes(self):
        analyzer = TalexFrictionAnalyzerKix()
        friction = {"code": "ERR-KIX-GIT-MERGE-LOCAL-CHANGES"}
        result = analyzer.propose_correction(friction)
        assert result["action"] == "stash_before_switch"
        assert result["atomic"] is True

    def test_propose_correction_err_kix_hook_bash_on_windows(self):
        analyzer = TalexFrictionAnalyzerKix()
        friction = {"code": "ERR-KIX-HOOK-BASH-ON-WINDOWS"}
        result = analyzer.propose_correction(friction)
        assert result["action"] == "convert_to_python"
        assert result["atomic"] is True

    def test_propose_correction_unknown_code(self):
        analyzer = TalexFrictionAnalyzerKix()
        friction = {"code": "ERR-UNKNOWN"}
        result = analyzer.propose_correction(friction)
        assert result["action"] == "manual_review"

    def test_analyze_with_frictions(self):
        analyzer = TalexFrictionAnalyzerKix()
        context = {
            "frictions": [
                {"code": "ERR-001", "severity": "high", "structural": True, "causal": True},
                {"code": "ERR-999", "severity": "low", "structural": False, "causal": False},
            ]
        }
        result = analyzer.analyze(context)
        assert result["status"] == "COMPLETED"
        assert result["summary"]["total"] == 2
        assert result["summary"]["known"] == 1
        assert result["summary"]["unknown"] == 1

    def test_export_report(self, tmp_path):
        analyzer = TalexFrictionAnalyzerKix()
        context = {
            "frictions": [
                {"code": "ERR-001", "severity": "high", "structural": True, "causal": True},
            ]
        }
        with patch("src.kix.pipelines.talex_friction_analyzer.datetime") as mock_dt:
            mock_dt.now.return_value = __import__("datetime").datetime(2026, 1, 1, 0, 0, 0)
            output = analyzer.export_report(output_path=tmp_path / "report.json")
        assert output.exists()
        data = __import__("json").loads(output.read_text(encoding="utf-8"))
        assert data["status"] == "COMPLETED"

    def test_analyze_friction_entry_point(self):
        context = {
            "frictions": [
                {"code": "ERR-001", "severity": "high", "structural": True, "causal": True},
            ]
        }
        result = analyze_friction(context)
        assert result["status"] == "COMPLETED"
        assert result["summary"]["total"] == 1

    def test_main_block_execution(self):
        """Coverage for __main__ block (lines 167-240) using compile/exec pattern."""
        source = Path("src/kix/pipelines/talex_friction_analyzer.py").read_text(encoding="utf-8")
        code = compile(source, str(Path("src/kix/pipelines/talex_friction_analyzer.py")), "exec")
        
        mock_result = {
            "status": "COMPLETED",
            "summary": {"total": 7, "known": 5, "unknown": 2, "structural": 5, "causal": 7},
        }
        
        captured = []
        def mock_print(*args, **kwargs):
            captured.append(args[0] if args else "")
        
        with patch("src.kix.pipelines.talex_friction_analyzer.analyze_friction", return_value=mock_result):
            with patch("builtins.print", side_effect=mock_print):
                exec(code, {
                    "__name__": "__main__",
                    "__file__": str(Path("src/kix/pipelines/talex_friction_analyzer.py")),
                    "analyze_friction": analyze_friction,
                    "print": mock_print,
                })
        
        assert len(captured) >= 1
        assert captured[0].startswith("[ACT-017]")
        assert "COMPLETED" in captured[0]
