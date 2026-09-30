#!/usr/bin/env python3
r"""
KG_L_Client — Client unifié pour KG-L Engine (Phase 2: Remote HTTP).

Fournit query(), get_hubs(), get_graph_stats(), ingest() en mode local
ET remote HTTP.

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
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import urllib.request
import urllib.error

# Add runtime to path for local mode
_RUNTIME_PATH = Path(__file__).resolve().parent.parent.parent.parent.parent / "kg_l" / "src" / "runtime"
_KG_L_PATH = Path(__file__).resolve().parent.parent.parent.parent.parent / "kg_l" / "src"
if str(_RUNTIME_PATH) not in sys.path:
    sys.path.insert(0, str(_RUNTIME_PATH))
if str(_KG_L_PATH) not in sys.path:
    sys.path.insert(0, str(_KG_L_PATH))

try:
    from kg_l import KGLEngine as _KGLEngine
except (ImportError, ModuleNotFoundError):  # pragma: no cover - optional dependency
    _KGLEngine = None


class KG_L_Client:
    """Client unifié pour le moteur KG-L.
    
    Peut fonctionner en mode local (in-process) ou remote (HTTP).
    Config injectée via settings.yaml ou paramètres.
    """
    
    def __init__(self, host: str = "http://localhost:8888", data_path: str = None, timeout: int = 10):
        self.host = host
        self.timeout = timeout
        self._local_engine = None
        self._mode = "remote"
        
        # If host is "local" or data_path given, try local mode first
        if host == "local" or (data_path and "localhost" in host):
            if _KGLEngine is None:
                raise RuntimeError(
                    "KG-L local mode requested but kg_l is not available. "
                    "Install kg_l or use host='http://localhost:8888' for remote mode."
                )
            try:
                self._local_engine = _KGLEngine(data_path or "kg_l/data")
                self._mode = "local"
            except Exception as e:
                print(f"[KG_L_Client] Fallback to remote mode: {e}")
                self._mode = "remote"
        else:
            self._mode = "remote"
    
    def _remote_get(self, endpoint: str) -> dict:
        """Effectue un appel GET en mode remote."""
        req = urllib.request.Request(f"{self.host}{endpoint}", method="GET")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise RuntimeError(f"KG-L remote unreachable: {exc}") from exc
        except TimeoutError:
            raise RuntimeError(f"KG-L remote timeout after {self.timeout}s")
    
    def _remote_post(self, endpoint: str, payload: dict) -> dict:
        """Effectue un appel POST en mode remote."""
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.host}{endpoint}",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise RuntimeError(f"KG-L remote unreachable: {exc}") from exc
        except TimeoutError:
            raise RuntimeError(f"KG-L remote timeout after {self.timeout}s")
    
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
            # Remote HTTP call
            payload = {"cypher": cypher, "params": params or {}}
            result = self._remote_post("/query", payload)
            return result.get("results", [])
    
    def get_hubs(self, limit: int = 50, min_degree: int = 2) -> list:
        """Get top hubs by degree."""
        if self._mode == "local" and self._local_engine:
            return self._local_engine.get_hubs(limit=limit, min_degree=min_degree)
        # Remote mode
        result = self._remote_get(f"/hubs?limit={limit}&min_degree={min_degree}")
        return result.get("hubs", [])
    
    def get_graph_stats(self) -> Dict:
        """Return graph statistics (nodes, edges, components, chi)."""
        if self._mode == "local" and self._local_engine:
            return self._local_engine.get_graph_stats()
        # Remote mode
        result = self._remote_get("/stats")
        return result
    
    def ingest(self, anchors: list, edges: list = None) -> Dict:
        """Ingest anchors and edges."""
        if self._mode == "local" and self._local_engine:
            return self._local_engine.ingest(anchors, edges)
        # Remote mode
        payload = {"anchors": anchors, "edges": edges or []}
        result = self._remote_post("/ingest", payload)
        return result
    
    def health(self) -> Dict:
        """Check KG-L engine health."""
        if self._mode == "local" and self._local_engine:
            return {"status": "ok", "mode": "local"}
        try:
            return self._remote_get("/health")
        except Exception as exc:
            return {"status": "unreachable", "error": str(exc)}
