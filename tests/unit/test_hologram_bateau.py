"""Tests for src/holograms/bateau.py."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from src.holograms.bateau import (
    _scan_ancre,
    _scan_coque,
    _scan_equipage,
    _scan_gouvernail,
    _scan_pilote,
    _scan_vagues,
    _scan_vigie,
    holographe_bateau,
    main,
)


class TestHolographeBateau:
    def test_missing_repo(self, tmp_path):
        result = holographe_bateau(tmp_path / "missing")
        assert result["hologramme"] is None
        assert "Repo not found" in result["error"]

    def test_full_hologram(self, tmp_path):
        (tmp_path / "MANIFEST.yaml").write_text("name: test\n")
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("print('hello')\n")
        (tmp_path / "tests").mkdir()
        result = holographe_bateau(tmp_path)
        assert "coque" in result
        assert "vagues" in result
        assert result["vagues"]["count"] >= 1

    def test_zone_filter(self, tmp_path):
        (tmp_path / "MANIFEST.yaml").write_text("name: test\n")
        result = holographe_bateau(tmp_path)
        coque = result.get("coque")
        assert coque is not None
        assert coque["type"] == "registre"


class TestScanCoque:
    def test_manifest_found(self, tmp_path):
        (tmp_path / "MANIFEST.yaml").write_text("name: test\n")
        result = _scan_coque(tmp_path)
        assert result["source"].endswith("MANIFEST.yaml")
        assert result["type"] == "registre"

    def test_manifest_missing(self, tmp_path):
        result = _scan_coque(tmp_path)
        assert result["found"] is False


class TestScanVagues:
    def test_src_exists(self, tmp_path):
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("print('hello')\n")
        result = _scan_vagues(tmp_path)
        assert result["count"] >= 1

    def test_src_missing(self, tmp_path):
        result = _scan_vagues(tmp_path)
        assert result["count"] == 0


class TestScanGouvernail:
    def test_tests_dir_exists(self, tmp_path):
        (tmp_path / "tests").mkdir()
        result = _scan_gouvernail(tmp_path)
        assert result["tests_dir"] is True

    def test_tests_dir_missing(self, tmp_path):
        result = _scan_gouvernail(tmp_path)
        assert result["tests_dir"] is False


class TestScanVigie:
    def test_seeker_found(self, tmp_path):
        (tmp_path / "coverage.json").write_text("{}")
        result = _scan_vigie(tmp_path)
        assert len(result["seekers_found"]) >= 1

    def test_seeker_missing(self, tmp_path):
        result = _scan_vigie(tmp_path)
        assert result["seekers_found"] == []


class TestScanAncre:
    def test_wal_files_found(self, tmp_path):
        (tmp_path / "session.wal").write_text("{}")
        result = _scan_ancre(tmp_path)
        assert result["wal_files"] >= 1

    def test_wal_files_missing(self, tmp_path):
        result = _scan_ancre(tmp_path)
        assert result["wal_files"] == 0


class TestScanEquipage:
    def test_agents_found(self, tmp_path):
        (tmp_path / "agents").mkdir()
        result = _scan_equipage(tmp_path)
        assert len(result["dirs_found"]) >= 1

    def test_agents_missing(self, tmp_path):
        result = _scan_equipage(tmp_path)
        assert result["dirs_found"] == []


class TestScanPilote:
    def test_pilots_found(self, tmp_path):
        (tmp_path / "audit").mkdir()
        result = _scan_pilote(tmp_path)
        assert len(result["scripts_found"]) >= 1

    def test_pilots_missing(self, tmp_path):
        result = _scan_pilote(tmp_path)
        assert result["scripts_found"] == []


class TestMain:
    def test_main_zone_filter(self, tmp_path):
        (tmp_path / "MANIFEST.yaml").write_text("name: test\n")
        with patch("sys.argv", ["bateau.py", "--repo", str(tmp_path), "--zone", "coque"]):
            with patch("builtins.print") as mock_print:
                main()
        mock_print.assert_called_once()
        printed = mock_print.call_args[0][0]
        assert "registre" in printed
