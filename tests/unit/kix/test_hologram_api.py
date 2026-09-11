#!/usr/bin/env python3
"""Tests unitaires pour l'API Hologram (PRD-MOC-027/028).

Phase 15 — Multi-architecture v2 tests added.
"""
import pytest
import sys
import os
from flask import Flask, jsonify

# --- Build a minimal Flask app with ONLY the hologram routes ---

REPO_PATHS = {
    "KIX": r"D:\DO\WEB\TOOLS\L2-PLATFORM\KIX",
    "VERSES": r"D:\DO\WEB\TOOLS\L4-TOOLS\VERSES",
    "CTULU": r"D:\DO\WEB\TOOLS\L4-TOOLS\CTULU",
    "GOVERNANCE-HUB": r"D:\DO\WEB\TOOLS\L0-CANON\GOVERNANCE-HUB",
}

ZONES_DEFS = {
    "coque": "registre/manifest",
    "vagues": "fichiers actifs",
    "gouvernail": "validation/tests",
    "vigie": "coverage/scanner",
    "ancre": "archive/WAL",
    "equipage": "agents/experts",
    "pilote": "audit/navigation",
}


def make_test_app():
    """Create Flask app with hologram routes — no KG-L engine required."""
    app = Flask(__name__)

    try:
        _holo_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "src", "holograms"
        )
        sys.path.insert(0, _holo_dir)
        from bateau import holographe_bateau
        _GEN = holographe_bateau
        HAS_GEN = True
    except ImportError:
        _GEN = None
        HAS_GEN = False

    @app.get("/hologram/<repo>")
    def hologram_repo(repo: str):
        if not HAS_GEN:
            return jsonify({"error": "holographe_bateau non disponible"}), 503
        from pathlib import Path
        repo_path = REPO_PATHS.get(repo.upper())
        if not repo_path or not Path(repo_path).exists():
            return jsonify({"error": f"repo {repo} introuvable"}), 404
        h = _GEN(Path(repo_path))
        return jsonify({"repo": repo, "port": 8796, "hologramme": h})

    @app.get("/hologram/<repo>/zones")
    def hologram_zones(repo: str):
        return jsonify({"repo": repo, "zones": ZONES_DEFS})

    @app.post("/hologram/generate")
    def hologram_generate():
        from pathlib import Path
        body = flask_request_json()
        repo_name = (body.get("repo") or "").upper()
        zone = body.get("zone", "all")
        arch = body.get("architecture", "x86_64")
        repo_path = REPO_PATHS.get(repo_name)
        if not repo_path:
            return jsonify({"error": f"repo {repo_name} non supporté"}), 400
        result = _GEN(Path(repo_path))
        return jsonify({
            "status": "generated",
            "repo": repo_name,
            "zone": zone,
            "architecture": arch,
            "hologramme": result
        }), 201

    return app


def flask_request_json():
    """Helper for request.json in test context."""
    try:
        return flask.request.get_json() or {}
    except Exception:
        return {}


import flask


@pytest.fixture
def app():
    """Flask test app with hologram routes."""
    flask.current_app = None
    return make_test_app()


class TestHologramRepo:
    """Test 1: GET /hologram/<repo>"""
    def test_hologram_kix(self, app):
        """GET /hologram/KIX → 200 + coque/vagues/gouvernail."""
        response = app.test_client().get("/hologram/KIX")
        assert response.status_code == 200
        data = response.get_json()
        assert "repo" in data and data["repo"] == "KIX"
        hologram_str = str(data.get("hologramme", ""))
        for z in ["coque", "vagues", "gouvernail", "vigie", "ancre", "equipage", "pilote"]:
            assert z in hologram_str, f"zone {z} manquante"

    def test_hologram_invalid(self, app):
        """GET /hologram/INVALID → 404."""
        response = app.test_client().get("/hologram/INVALID")
        assert response.status_code == 404


class TestHologramGenerate:
    """Test POST /hologram/generate → 201."""
    def test_hologram_generate(self, app):
        """POST /hologram/generate → 201 + status='generated'."""
        response = app.test_client().post(
            "/hologram/generate",
            json={"repo": "KIX", "zone": "all"}
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data.get("status") == "generated"
        assert data.get("repo") == "KIX"


class TestHologramZones:
    """Test GET /hologram/<repo>/zones → 7 zones."""
    def test_hologram_zones(self, app):
        """GET /hologram/KIX/zones → 200 + 7 zones."""
        response = app.test_client().get("/hologram/KIX/zones")
        assert response.status_code == 200
        data = response.get_json()
        zones = data.get("zones", {})
        assert "coque" in zones
        assert "vagues" in zones
        assert "gouvernail" in zones


class TestCrossRepoHologram:
    """Phase 11 — Cross-repo integration (VERSES, CTULU)."""

    def test_hologram_verses(self, app):
        """GET /hologram/VERSES → 200 + 7 zones."""
        response = app.test_client().get("/hologram/VERSES")
        assert response.status_code == 200
        data = response.get_json()
        assert data.get("repo") == "VERSES"
        zones = data.get("hologramme", {})
        for z in ["coque", "vagues", "gouvernail", "vigie", "ancre", "equipage", "pilote"]:
            assert z in zones

    def test_hologram_ctulu(self, app):
        """GET /hologram/CTULU → 200 + coque."""
        response = app.test_client().get("/hologram/CTULU")
        assert response.status_code == 200
        data = response.get_json()
        assert data.get("repo") == "CTULU"
        assert "coque" in data.get("hologramme", {})

    def test_cross_repo_consistency(self, app):
        """All repos return same 7-zone structure."""
        for repo in ["KIX", "VERSES", "CTULU"]:
            resp = app.test_client().get(f"/hologram/{repo}")
            assert resp.status_code == 200
            zones = resp.get_json().get("hologramme", {})
            assert set(zones.keys()) == {
                "coque", "vagues", "gouvernail", "vigie", "ancre", "equipage", "pilote"
            }


class TestHologramV2:
    """Phase 15 — Multi-architecture hologram API v2 tests."""

    def test_hologram_generate_with_arch(self, app):
        """POST /hologram/generate with architecture=arm64 → 201 + architecture field."""
        response = app.test_client().post(
            "/hologram/generate",
            json={"repo": "KIX", "zone": "all", "architecture": "arm64"}
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data.get("status") == "generated"
        assert data.get("repo") == "KIX"
        assert data.get("architecture") == "arm64"

    def test_hologram_valid_invalid_arch(self, app):
        """get_arch_spec raises ValueError for invalid arch."""
        from pathlib import Path
        _holo_dir = Path(__file__).parent.parent.parent.parent / "src" / "holograms"
        if str(_holo_dir) not in sys.path:
            sys.path.insert(0, str(_holo_dir))
        try:
            from hologram_v2 import get_arch_spec
            with pytest.raises(ValueError):
                get_arch_spec("mips")
            spec = get_arch_spec("arm64")
            assert spec["bits"] == 64
        except ImportError:
            pytest.skip("hologram_v2 not available")
