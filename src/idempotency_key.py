"""
Clé d'idempotence pour KIX ⇄ ENV3.

Garantit qu'une exécution de runner est dédoublonnable via UUID par exécution.
"""
from __future__ import annotations

import uuid
from datetime import datetime


def generate_execution_id() -> str:
    """Générer un UUID d'exécution pour dédoublonnage."""
    return str(uuid.uuid4())


def generate_idempotency_key(intent_hash: str, execution_id: str) -> str:
    """Générer une clé d'idempotence à partir d'un IntentHash et d'un execution_id."""
    return f"{intent_hash}:{execution_id}:{datetime.utcnow().isoformat()}Z"
