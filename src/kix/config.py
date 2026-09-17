"""Configuration centralisée KIX via Pydantic Settings.

IntentHash: 0xPRD_MOC_VOLTX_PHASE3_RUNNERS_STANDARD_20260905
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings centralisés KIX."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Chemins
    config_dir: Path = Path(__file__).resolve().parent.parent.parent / "config"
    runners_dir: Path = Path(__file__).resolve().parent.parent.parent / "runners"

    # KG-L
    kg_l_graph: Optional[Path] = None

    # WAZAA
    wazaa_url: Optional[str] = None

    # Logging
    log_level: str = "INFO"
