#!/usr/bin/env python3
r"""
VaultWriter — Writer unifié pour le vault VOLTX (Phase 1)
Fournit write_auto_index(), write_note(), write_hub().

ERR_030: UTF-8 wrapper included.
"""
import io
import sys
import hashlib
from pathlib import Path
from typing import Optional

# ERR_030 FIX
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', effects='replace')


class VaultWriter:
    """Writer unifié pour le vault VOLTX.
    
    Centralise toutes les operations d'ecriture dans le vault.
    Config injectée via settings.yaml.
    
    Methods:
    - write_auto_index(content): write VOLTX/00-Index/auto-index.md
    - write_note(path, content): write arbitrary note
    - write_hub(hub_id, content): write hub page
    """
    
    def __init__(self, vault_path: str = None):
        self.vault_path = Path(vault_path or "D:/DO/WEB/TOOLS/L0-CANON/VOLTX")
        self._ensure_dirs()
    
    def _ensure_dirs(self):
        """Create required directories."""
        dirs = [
            "00-Index",
            "01-Hubs",
            "02-Concepts",
            "03-Projects",
            "notes"
        ]
        for d in dirs:
            (self.vault_path / d).mkdir(parents=True, exist_ok=True)
    
    def write_auto_index(self, content: str) -> Path:
        """Write auto-index to VOLTX/00-Index/auto-index.md."""
        output_path = self.vault_path / "00-Index" / "auto-index.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        return output_path
    
    def write_note(self, path: str, content: str) -> Path:
        """Write arbitrary note to vault."""
        full_path = self.vault_path / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        return full_path
    
    def write_hub(self, hub_id: str, content: str) -> Path:
        """Write hub page to VOLTX/01-Hubs/{hub_id}.md."""
        safe_id = hub_id.replace("/", "_").replace("\\", "_")
        output_path = self.vault_path / "01-Hubs" / f"{safe_id}.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        return output_path
    
    def compute_hash(self, content: str) -> str:
        """Compute SHA256 hash of content."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
    
    def is_identical(self, path: Path, new_content: str) -> bool:
        """Check if new content is identical to existing (by hash)."""
        if not path.exists():
            return False
        existing = path.read_text(encoding="utf-8")
        return self.compute_hash(existing) == self.compute_hash(new_content)
