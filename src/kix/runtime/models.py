"""Modèles de données KG-L runtime.

IntentHash: 0xPRD_MOC_GEN_025_KG_L_GOVERNANCE_WIRING_20260827
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class KG_LNode:
    id: str
    name: str
    sources: List[str] = field(default_factory=lambda: ["known_repositories"])
    layer: str = ""
    status: str = "ACTIVE"
    local_path: Optional[str] = None
    remote: Optional[str] = None
    role: str = ""
    intent_hash: str = ""
    logical_layers: List[str] = field(default_factory=list)
    entity_type: str = "REPO"


@dataclass
class KG_LGraph:
    generated_at_utc: str = ""
    count: int = 0
    nodes: List[KG_LNode] = field(default_factory=list)
