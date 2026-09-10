#!/usr/bin/env python3
r"""
KG_L_Client — Client unifié pour KG-L Engine (Phase 1)
Fournit query(), get_hubs(), get_graph_stats(), ingest().

ERR_030: UTF-8 wrapper included.
"""
import io
import sys
import json
from pathlib import Path
from typing import Optional, Dict, List

# ERR_030 FIX
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', effects='replace')

# Add shared-clients to path — local kg_l.py contains KGLEngine (ERR_054-fix)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kg_l import KGLEngine as _KGLEngine


class KG_L_Client:
    """Client unifié pour le moteur KG-L.
    
    Peut fonctionner en mode local (in-process) ou remote (HTTP).
    Config injectée via settings.yaml.
    """
    
    def __init__(self, host: str = "http://localhost:8888", data_path: str = None):
        self.host = host
        self._local_engine = None
        
        # If host is "local" or data_path given, use in-process engine
        if host == "local" or (data_path and "localhost" in host):
            try:
                self._local_engine = _KGLEngine(data_path or "kg_l/data")
                self._mode = "local"
            except Exception as e:
                print(f"[KG_L_Client] Fallback to remote mode: {e}")
                self._mode = "remote"
        else:
            self._mode = "remote"
    
    def query(self, cypher: str, params: dict = None) -> List[Dict]:
        """Execute Cypher query. Returns list of result dicts."""
        if self._mode == "local" and self._local_engine:
            result = self._local_engine.execute_cypher(cypher, params)
            if "results" in result:
                return result["results"]
            if "hubs" in result:
                return result["hubs"]
            return [result]
        else:
            # Remote HTTP call (stub)
            return []
    
    def get_hubs(self, limit: int = 50, min_degree: int = 2) -> list:
        """Get top hubs by degree."""
        if self._mode == "local" and self._local_engine:
            return self._local_engine.get_hubs(limit=limit, min_degree=min_degree)
        return []
    
    def get_graph_stats(self) -> Dict:
        """Return graph statistics (nodes, edges, components, chi)."""
        if self._mode == "local" and self._local_engine:
            return self._local_engine.get_graph_stats()
        return {"nodes": 0, "edges": 0, "components": 1, "chi": 2}
    
    def ingest(self, anchors: list, edges: list = None) -> Dict:
        """Ingest anchors and edges."""
        if self._mode == "local" and self._local_engine:
            return self._local_engine.ingest(anchors, edges)
        return {"status": "remote_mode", "ingested": 0}
