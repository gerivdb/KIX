"""
KG-L Client — Shared client for KG-L HTTP API.

Provides unified interface for querying KG-L graph database.
Replaces 4 duplicate implementations across the codebase.

IntentHash: 0xKIX_SHARED_KG_L_CLIENT_20260905
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

# requests is optional — fallback to local engine if absent (ERR_054-import)
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

logger = logging.getLogger(__name__)


class KGLEngine:
    """KG-L Engine — minimal local implementation for KIX standalone.

    Fallback when requests/HTTP unavailable (WSL2, CI, offline).
    IntentHash: 0xKIX_SHARED_KG_L_ENGINE_20260910
    """

    def __init__(self, data_path: str = "kg_l/data"):
        self.data_path = Path(data_path)
        self.data_path.mkdir(parents=True, exist_ok=True)
        self._nodes: Dict[str, Dict] = {}
        self._edges: List[Dict] = []

    def index_node(self, node_id: str, term: str, realm: str):
        """Index a node by term + realm."""
        if node_id not in self._nodes:
            self._nodes[node_id] = {"id": node_id, "terms": [], "realm": realm}
        self._nodes[node_id]["terms"].append(term)
        self._nodes[node_id]["realm"] = realm

    def get_by_term(self, term: str) -> List[str]:
        """Get node IDs matching a term."""
        return [nid for nid, node in self._nodes.items() if term in node.get("terms", [])]

    def get_hubs(self, limit: int = 50, min_degree: int = 2) -> List[Dict]:
        """Return top hubs by edge count."""
        degrees = {}
        for edge in self._edges:
            src = edge.get("src")
            dst = edge.get("dst")
            degrees[src] = degrees.get(src, 0) + 1
            degrees[dst] = degrees.get(dst, 0) + 1
        hubs = [{"id": nid, "degree": d} for nid, d in degrees.items() if d >= min_degree]
        return sorted(hubs, key=lambda x: x["degree"], reverse=True)[:limit]

    def get_graph_stats(self) -> Dict:
        """Return basic graph statistics."""
        return {
            "nodes": len(self._nodes),
            "edges": len(self._edges),
            "components": 1,
            "chi": 2,
        }

    def query(self, cypher: str, params: Optional[Dict] = None) -> List[Dict]:
        """Minimal query — returns indexed nodes."""
        term = (params or {}).get("term", cypher.split("WHERE")[-1].strip() if "WHERE" in cypher else "")
        if term:
            return [{"id": nid} for nid in self.get_by_term(term.strip())]
        return [{"id": nid, "data": data} for nid, data in self._nodes.items()]

    def ingest(self, anchors: List[str], edges: List[Dict] = None) -> Dict:
        """Ingest anchors + edges."""
        for anchor in anchors:
            self.index_node(anchor, anchor, "default")
        if edges:
            self._edges.extend(edges)
        return {"status": "ok", "nodes": len(self._nodes), "edges": len(self._edges)}


class KG_L_Client:
    """Client for KG-L HTTP API."""

    def __init__(
        self,
        base_url: str = "http://localhost:8888",
        timeout: int = 30,
        session: Optional[requests.Session] = None
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.timeout = timeout

    def query(
        self,
        cypher: str,
        params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query against KG-L.

        Args:
            cypher: Cypher query string
            params: Optional parameters for parameterized queries

        Returns:
            List of result dictionaries
        """
        payload = {"cypher": cypher}
        if params:
            payload["params"] = params

        try:
            resp = self.session.post(
                f"{self.base_url}/query",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("results", [])
        except requests.RequestException as e:
            logger.error(f"KG-L query failed: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"KG-L response decode failed: {e}")
            return []

    def query_gaps(self) -> List[Dict[str, Any]]:
        """
        Detect gaps in the KG-L graph.

        Returns:
            List of gaps with fields: id, type, title, labels, degree
            Types: "untyped", "orphan", "low_degree"
        """
        gaps = []

        # 1. Nodes without register (untyped)
        untyped = self.query("""
            MATCH (n)
            WHERE n.register IS NULL OR n.register = ""
            RETURN n.term AS id, n.definition AS title, n.register AS register, labels(n) AS labels
            LIMIT 100
        """)
        for node in untyped:
            gaps.append({
                "id": node.get("id", "unknown"),
                "title": node.get("title", ""),
                "type": "untyped",
                "register": node.get("register"),
                "labels": node.get("labels", [])
            })

        # 2. Orphan nodes (degree 0)
        orphans = self.query("""
            MATCH (n)
            WHERE NOT (n)--()
            RETURN n.term AS id, n.definition AS title, labels(n) AS labels
            LIMIT 50
        """)
        for node in orphans:
            gaps.append({
                "id": node.get("id", "unknown"),
                "title": node.get("title", ""),
                "type": "orphan",
                "labels": node.get("labels", [])
            })

        # 3. Low connectivity nodes (degree 1)
        low_degree = self.query("""
            MATCH (n)
            OPTIONAL MATCH (n)-[r]-()
            WITH n, count(r) AS degree
            WHERE degree > 0 AND degree < 2
            RETURN n.term AS id, n.definition AS title, degree, labels(n) AS labels
            LIMIT 50
        """)
        for node in low_degree:
            gaps.append({
                "id": node.get("id", "unknown"),
                "title": node.get("title", ""),
                "type": "low_degree",
                "degree": node.get("degree", 0),
                "labels": node.get("labels", [])
            })

        return gaps

    def count_nodes(self) -> int:
        """Return total node count."""
        results = self.query("MATCH (n) RETURN count(n) AS count")
        return results[0].get("count", 0) if results else 0

    def count_edges(self) -> int:
        """Return total edge count."""
        results = self.query("MATCH ()-[r]->() RETURN count(r) AS count")
        return results[0].get("count", 0) if results else 0

    def get_graph_stats(self) -> Dict[str, Any]:
        """Return complete graph statistics."""
        stats = {}
        stats["nodes"] = self.count_nodes()
        stats["edges"] = self.count_edges()
        stats["components"] = 1  # Approximation
        stats["chi"] = stats["nodes"] - stats["edges"] + stats["components"]
        return stats

    def health(self) -> bool:
        """Check KG-L health."""
        try:
            resp = self.session.get(f"{self.base_url}/health", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="KG-L Client test")
    parser.add_argument("--url", default="http://localhost:8888", help="KG-L URL")
    parser.add_argument("--query", default="MATCH (n) RETURN count(n) AS count", help="Cypher query")
    args = parser.parse_args()

    client = KG_L_Client(args.url)
    result = client.query(args.query)
    print(json.dumps(result, indent=2))