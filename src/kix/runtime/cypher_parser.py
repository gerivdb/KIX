"""Parser Cypher KG-L (stub).

IntentHash: 0xPRD_MOC_GEN_025_KG_L_GOVERNANCE_WIRING_20260827
"""

from __future__ import annotations

import re
from typing import List


class CypherStatement:
    def __init__(self, raw: str) -> None:
        self.raw = raw.strip()

    def __repr__(self) -> str:
        return f"CypherStatement({self.raw!r})"


def parse_cypher(text: str) -> List[CypherStatement]:
    """Parse basique d'un script Cypher en statements."""
    statements: List[CypherStatement] = []
    for chunk in re.split(r";\s*", text):
        chunk = chunk.strip()
        if chunk:
            statements.append(CypherStatement(chunk))
    return statements
