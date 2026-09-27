"""WAL journaling pour les actions doctor/self-healing KIX.

Enregistre chaque action de self-healing (restart, start, restore)
dans `data/kix-doctor.jsonl` pour audit et replay.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

WAL_DIR = Path(__file__).resolve().parent.parent / "data"
WAL_FILE = WAL_DIR / "kix-doctor.jsonl"


def log_wal(event_type: str, data: dict[str, Any]) -> None:
    """Logger un événement doctor/self-healing dans le WAL JSONL."""
    WAL_DIR.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "intent_hash": "0xPRD_MOC_KIX_EXE_ORCHESTRATION_20260924",
        "data": data,
    }
    with open(WAL_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def create_backup(file_path: str | Path) -> Path | None:
    """Créer un backup `.bak` atomique d'un fichier de config.

    Retourne le chemin du `.bak` créé, ou None si le fichier source n'existe pas.
    """
    src = Path(file_path)
    if not src.exists():
        return None
    backup_path = src.with_suffix(src.suffix + ".bak")
    backup_path.write_bytes(src.read_bytes())
    log_wal("backup_created", {
        "source": str(src),
        "backup": str(backup_path),
    })
    return backup_path


def restore_backup(file_path: str | Path) -> bool:
    """Restaurer un fichier depuis son `.bak`.

    Retourne True si la restauration a réussi, False sinon.
    """
    src = Path(file_path)
    backup_path = src.with_suffix(src.suffix + ".bak")
    if not backup_path.exists():
        return False
    src.write_bytes(backup_path.read_bytes())
    log_wal("backup_restored", {
        "source": str(src),
        "backup": str(backup_path),
    })
    return True


def get_wal_entries(event_type: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    """Lire les dernières entrées du WAL doctor.

    Si `event_type` est fourni, filtrer par type d'événement.
    """
    if not WAL_FILE.exists():
        return []
    entries: list[dict[str, Any]] = []
    with open(WAL_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            if event_type is None or entry.get("event_type") == event_type:
                entries.append(entry)
    return entries[-limit:]
