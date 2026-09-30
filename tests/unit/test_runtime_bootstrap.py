"""Tests for src/kix/runtime/bootstrap.py."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.kix.runtime import bootstrap


class TestBootstrapKgL:
    def test_bootstrap_success(self, monkeypatch, capsys):
        fake_result = MagicMock(ok=True, issues=[])
        monkeypatch.setattr(
            "src.kix.runtime.bootstrap.validate_kg_l_runtime",
            lambda graph_path, registry_path: fake_result,
        )
        exit_code = bootstrap.bootstrap_kg_l()
        captured = capsys.readouterr()
        assert exit_code == 0
        assert "KG-L-BOOT" in captured.out

    def test_bootstrap_failure_returns_one(self, monkeypatch, capsys):
        fake_result = MagicMock(ok=False, issues=["missing graph"])
        monkeypatch.setattr(
            "src.kix.runtime.bootstrap.validate_kg_l_runtime",
            lambda graph_path, registry_path: fake_result,
        )
        exit_code = bootstrap.bootstrap_kg_l()
        captured = capsys.readouterr()
        assert exit_code == 1
        assert "ISSUE" in captured.out

    def test_main_block_exits_with_bootstrap_code(self, monkeypatch):
        fake_result = MagicMock(ok=True, issues=[])
        monkeypatch.setattr(
            "src.kix.runtime.bootstrap.validate_kg_l_runtime",
            lambda graph_path, registry_path: fake_result,
        )
        source = Path(bootstrap.__file__).read_text(encoding="utf-8")
        code = compile(source, str(bootstrap.__file__), "exec")
        with patch.object(bootstrap.sys, "exit") as mock_exit:
            exec(
                code,
                {
                    "__name__": "__main__",
                    "__file__": str(bootstrap.__file__),
                },
            )
        mock_exit.assert_called_once_with(0)
