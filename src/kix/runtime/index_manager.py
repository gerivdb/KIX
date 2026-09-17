"""Index manager KG-L (stub).

IntentHash: 0xPRD_MOC_GEN_025_KG_L_GOVERNANCE_WIRING_20260827
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class IndexEntry:
    node_id: str
    layer: str
    status: str
    local_path: str
    remote: str


class KG_LIndexManager:
    def __init__(self) -> None:
        self.entries: List[IndexEntry] = []

    def index_nodes(self, nodes: List[Dict]) -> None:
        for node in nodes:
            if not isinstance(node, dict):
                continue
            self.entries.append(
                IndexEntry(
                    node_id=str(node.get("id", "")),
                    layer=str(node.get("layer", "")),
                    status=str(node.get("status", "")),
                    local_path=str(node.get("local_path", "")),
                    remote=str(node.get("remote", "")),
                )
            )

    def find_by_layer(self, layer: str) -> List[IndexEntry]:
        return [entry for entry in self.entries if entry.layer == layer]
