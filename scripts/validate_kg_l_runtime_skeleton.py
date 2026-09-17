"""Validation basique du runtime KG-L KIX (hors pytest)."""

from __future__ import annotations

import sys
from pathlib import Path

KIX_ROOT = Path(r"D:\DO\WEB\TOOLS\L2-PLATFORM\KIX")
sys.path.insert(0, str(KIX_ROOT))

from src.kix.runtime.models import Anchor, Edge, QueryRequest, ParsedQuery
from src.kix.runtime.validation import validate_anchor, validate_graph
from src.kix.runtime.cypher_parser import CypherParser
from src.kix.runtime.index_manager import IndexManager


def test_models() -> bool:
    anchor = Anchor(id="kg-l", name="KG-L", layer="L4-TOOLS")
    assert anchor.id == "kg-l"
    assert anchor.layer == "L4-TOOLS"
    edge = Edge(source="kg-l", target="KIX", relation="serves")
    assert edge.relation == "serves"
    return True


def test_validation() -> bool:
    result = validate_anchor({"term": "kg-l", "name": "KG-L", "layer": "L4-TOOLS"})
    assert result.ok
    bad = validate_anchor({"name": "KG-L"})
    assert not bad.ok
    return True


def test_parser() -> bool:
    parser = CypherParser()
    query = parser.parse("MATCH (n) RETURN n")
    assert len(query.match_patterns) == 1
    assert len(query.return_projections) == 1
    return True


def test_index_manager() -> bool:
    idx = IndexManager()
    idx.rebuild({"a": {"layer": "L4"}, "b": {"layer": "L2"}})
    assert "a" in idx._term_index
    assert "L4" in idx._register_index
    return True


if __name__ == "__main__":
    results = [
        test_models(),
        test_validation(),
        test_parser(),
        test_index_manager(),
    ]
    print(f"KG-L runtime validation: {sum(results)}/{len(results)} passed")
    sys.exit(0 if all(results) else 1)
