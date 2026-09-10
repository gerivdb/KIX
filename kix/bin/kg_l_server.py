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

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from kg_l import KGLEngine


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
    
    return app, engine


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
