#!/usr/bin/env python3
r"""
KG-L Server — Flask OpenAPI 3.0 Server (port 8796)

Endpoints:
  GET  /health         — health check
  GET  /metrics        — Prometheus metrics
  GET  /openapi.json   — OpenAPI 3.0 spec
  POST /query          — execute Cypher query
  POST /ingest         — ingest anchors + edges
  GET  /hubs           — get top hubs
  GET  /gaps           — get graph gaps
  GET  /stats          — graph statistics
  GET  /registry/anchors — list anchors
  GET  /registry/edges   — list edges

ERR_030 FIX: UTF-8 wrapper included.
"""
import io
import sys
import json
import time
import threading
from pathlib import Path

# ERR_030 FIX: Force UTF-8 on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add libs to path — KIX structure
_KIX_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_KIX_ROOT / "libs" / "src"))
sys.path.insert(0, str(_KIX_ROOT / "libs" / "shared-clients"))

from kg_l_client import KGLEngine


def create_app():
    """Create Flask app with OpenAPI 3.0."""
    try:
        from flask import Flask, request, jsonify
        from flask_openapi3 import OpenAPI, Info, MERGED
    except ImportError:
        # Fallback to minimal mock
        return create_mock_app()
    
    info = Info(
        title="KG-L Engine API",
        version="2.0.0",
        description="Knowledge Graph Logic Engine — Cypher parser, index, ACID, validation"
    )
    
    app = OpenAPI(__name__, info=info)
    engine = KGLEngine()
    
    # OpenAPI schema for endpoints
    query_schema = {
        "type": "object",
        "required": ["query"],
        "properties": {
            "query": {"type": "string", "description": "Cypher query"},
            "params": {"type": "object", "description": "Query parameters"}
        }
    }
    
    ingest_schema = {
        "type": "object",
        "properties": {
            "anchors": {
                "type": "array",
                "items": {"type": "object", "required": ["id", "term", "register"]}
            },
            "edges": {
                "type": "array",
                "items": {"type": "object", "required": ["source", "edge_type", "target"]}
            }
        }
    }
    
    @app.get("/health")
    def health():
        """Health check endpoint."""
        return jsonify({
            "status": "healthy",
            "service": "kg-l-engine",
            "version": "2.0.0",
            "build": datetime.utcnow().strftime("%Y%m%dT%H%M%SZ"),
            "uptime_seconds": time.time() - engine.data_path.stat().st_ctime
        })
    
    @app.get("/metrics")
    def metrics():
        """Prometheus metrics."""
        stats = engine.get_graph_stats()
        return jsonify({
            "kg_l_nodes_total": stats["nodes"],
            "kg_l_edges_total": stats["edges"],
            "kg_l_hubs_count": len(stats.get("hubs", [])),
            "kg_l_gaps_count": len(engine.get_gaps())
        })
    
    @app.post("/query")
    def query():
        """Execute Cypher query."""
        body = request.json or {}
        q = body.get("query", "")
        params = body.get("params", {})
        
        if not q:
            return jsonify({"error": "query is required"}), 400
        
        result = engine.execute_cypher(q, params)
        return jsonify(result)
    
    @app.post("/ingest")
    def ingest():
        """Ingest anchors and edges."""
        body = request.json or {}
        result = engine.ingest(
            anchors=body.get("anchors", []),
            edges=body.get("edges", [])
        )
        return jsonify(result)
    
    @app.get("/hubs")
    def hubs():
        """Get top hubs by degree."""
        min_degree = request.args.get("min_degree", 2, type=int)
        limit = request.args.get("limit", 50, type=int)
        result = engine.get_hubs(min_degree=min_degree, limit=limit)
        return jsonify({"hubs": result, "count": len(result)})
    
    @app.get("/gaps")
    def gaps():
        """Get graph gaps."""
        result = engine.get_gaps()
        return jsonify({"gaps": result, "count": len(result)})
    
    @app.get("/stats")
    def stats():
        """Get graph statistics."""
        result = engine.get_graph_stats()
        return jsonify(result)
    
    # Register holgram routes (port 8796)
    create_hologram_routes(app, engine)
    
    return app, engine


# =====================================================
# HOLOGRAM API (PRD-MOC-027/028) — port 8796
# IntentHash: 0xPRD_MOC_028_VOLTX_HOLO_20260910
# =====================================================

def create_hologram_routes(app, engine):
    """Add hologram endpoints to Flask app (port 8796)."""
    try:
        import sys, os
        _kix_src = os.path.join(os.path.dirname(__file__), "..", "..", "src")
        if _kix_src not in sys.path:
            sys.path.insert(0, _kix_src)
        from holograms.bateau import holographe_bateau
        HAS_GENERATOR = True
    except ImportError:
        HAS_GENERATOR = False

    @app.get("/hologram/<repo>")
    def hologram_repo(repo: str):
        """Retourne l'hologramme bateau d'un repo.

        GET /hologram/KIX
        GET /hologram/VERSES
        GET /hologram/CTULU
        """
        if not HAS_GENERATOR:
            return jsonify({"error": "holographe_bateau non disponible"}), 503

        try:
            from pathlib import Path
            # Repo path mapping (voltx:8796)
            repo_paths = {
                "KIX": Path(r"D:\DO\WEB\TOOLS\L2-PLATFORM\KIX"),
                "VERSES": Path(r"D:\DO\WEB\TOOLS\L4-TOOLS\VERSES"),
                "CTULU": Path(r"D:\DO\WEB\TOOLS\L4-TOOLS\CTULU"),
                "GOVERNANCE-HUB": Path(r"D:\DO\WEB\TOOLS\L0-CANON\GOVERNANCE-HUB"),
            }
            repo_path = repo_paths.get(repo.upper())
            if not repo_path or not repo_path.exists():
                return jsonify({"error": f"repo {repo} introuvable"}), 404

            hologramme = holographe_bateau(repo_path)
            return jsonify({"repo": repo, "port": 8796, "hologramme": hologramme})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.get("/hologram/<repo>/zones")
    def hologram_zones(repo: str):
        """Liste les 7 zones holographiques d'un repo."""
        zones_def = {
            "coque": "registre/manifest",
            "vagues": "fichiers actifs",
            "gouvernail": "validation/tests",
            "vigie": "coverage/scanner",
            "ancre": "archive/WAL",
            "equipage": "agents/experts",
            "pilote": "audit/navigation",
        }
        return jsonify({"repo": repo, "zones": zones_def})

    @app.post("/hologram/generate")
    def hologram_generate():
        """Génère un hologramme via CTULU/tools/holographe_bateau.py.

        POST /hologram/generate
        Body: {"repo": "KIX", "zone": "all"}
        """
        body = request.json or {}
        repo_name = (body.get("repo") or "").upper()
        zone = body.get("zone", "all")

        if not HAS_GENERATOR:
            return jsonify({"error": "generator non disponible"}), 503

        repo_paths = {
            "KIX": Path(r"D:\DO\WEB\TOOLS\L2-PLATFORM\KIX"),
            "VERSES": Path(r"D:\DO\WEB\TOOLS\L4-TOOLS\VERSES"),
            "CTULU": Path(r"D:\DO\WEB\TOOLS\L4-TOOLS\CTULU"),
            "GOVERNANCE-HUB": Path(r"D:\DO\WEB\TOOLS\L0-CANON\GOVERNANCE-HUB"),
        }
        repo_path = repo_paths.get(repo_name)
        if not repo_path:
            return jsonify({"error": f"repo {repo_name} non supporté"}), 400

        try:
            result = holographe_bateau(repo_path)
            return jsonify({"status": "generated", "repo": repo_name, "zone": zone, "hologramme": result}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500


def create_mock_app():
    """Minimal mock app for environments without Flask."""
    class MockApp:
        def __init__(self):
            self.engine = KGLEngine()

        def run(self, *args, **kwargs):
            print("[KG-L] Server mock — Flask not installed")

    return MockApp(), KGLEngine()


if __name__ == "__main__":
    from datetime import datetime
    
    app, engine = create_app()
    
    if hasattr(app, "run"):
        # Real Flask app
        app.run(host="0.0.0.0", port=8796, debug=False)
    else:
        # Mock mode
        print("[KG-L] Mock server (install flask flask-openapi3 for real server)")
        print(f"[KG-L] Engine stats: {engine.get_graph_stats()}")
