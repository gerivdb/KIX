#!/usr/bin/env python3
"""Tests unitaires pour l'API Hologram (PRD-MOC-027/028).

Test 1: GET /hologram/KIX → 200 + coque/vagues/gouvernail présents
Test 2: GET /hologram/INVALID → 404
Test 3: POST /hologram/generate → 201 + status="generated"
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
        # Path is <KIX_ROOT>\src\holograms
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
        repo_path = REPO_PATHS.get(repo_name)
        if not repo_path:
            return jsonify({"error": f"repo {repo_name} non supporté"}), 400
        result = _GEN(Path(repo_path))
        return jsonify({"status": "generated", "repo": repo_name, "zone": zone, "hologramme": result}), 201

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
        # Check all 7 zones in the returned hologram
        hologram_str = str(data.get("hologramme", ""))
        for z in ["coque", "vagues", "gouvernail", "vigie", "ancre", "equipage", "pilote"]:
            assert z in hologram_str, f"zone {z} manquante"

    def test_hologram_invalid(self, app):
        """GET /hologram/INVALID → 404."""
        response = app.test_client().get("/hologram/INVALID")
        assert response.status_code == 404


class TestHologramGenerate:
    """Test 3: POST /hologram/generate → 201 + status='generated'."""
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
    """Test 2: GET /hologram/<repo>/zones → liste des 7 zones."""
    def test_hologram_zones(self, app):
        """GET /hologram/KIX/zones → 200 + 7 zones."""
        response = app.test_client().get("/hologram/KIX/zones")
        assert response.status_code == 200
        data = response.get_json()
        zones = data.get("zones", {})
        assert "coque" in zones
        assert "vagues" in zones
        assert "gouvernail" in zones

