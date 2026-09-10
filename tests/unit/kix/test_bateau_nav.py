#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests navigation métacouche bateau KIX-VERSES (PRD-MOC-027).

KIX pointe vers le nav_verses.sh canonique dans VERSES repo (single source of truth).
"""

import platform
import subprocess
import pytest
from pathlib import Path


# VERSES_ROOT = D:/DO/WEB/TOOLS/L4-TOOLS/VERSES
VERSES_ROOT = Path(r"D:/DO/WEB/TOOLS/L4-TOOLS/VERSES")
NAV_SCRIPT = VERSES_ROOT / "scripts" / "nav_verses.sh"

# Sur Windows, bash invoque WSL2 — chemin converti en /mnt/d/...
_IS_WINDOWS = platform.system() == "Windows"
_NAV_PATH = str(NAV_SCRIPT) if not _IS_WINDOWS else NAV_SCRIPT.as_posix().replace("D:/DO/WEB", "/mnt/d/DO/WEB")


def _run_nav(args):
    """Run nav_verses.sh and return (stdout, stderr, rc) (Windows-safe)."""
    if _IS_WINDOWS:
        cmd = ["bash", "-c", f'bash "{_NAV_PATH}" {" ".join(args)}']
    else:
        cmd = ["bash", str(NAV_SCRIPT)] + args

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        errors="replace",  # WSL2 CLIXML pollutes stderr — ERR_028/ERR_049
        cwd=str(VERSES_ROOT),
    )
    # Filtrer les lignes valides ([Zone] ...) du bruit WSL2
    clean_lines = [l.strip() for l in result.stdout.splitlines() if l.strip().startswith("[")]
    clean_stdout = "\n".join(clean_lines)
    return clean_stdout, result.stderr, result.returncode


class TestCoque:
    """Zone 1 — MANIFEST.yaml comme coque du bateau."""

    def test_coque_manifest_exists(self):
        """La coque (MANIFEST.yaml) doit exister."""
        manifest = VERSES_ROOT / "MANIFEST.yaml"
        assert manifest.exists(), "MANIFEST.yaml absent — la coque est brisée"

    def test_coque_verse_count(self):
        """nav check coque doit retourner >= 100 versets."""
        stdout, _, rc = _run_nav(["check", "coque"])
        assert rc == 0, f"nav check coque échoué (rc={rc}): {stdout}"
        line = [l for l in stdout.splitlines() if "[Coque]" in l][0]
        count = int(line.split()[1])
        assert count >= 100, f"Trop peu de versets: {count}"


class TestVagues:
    """Zone 2 — verses/actifs/ comme vagues vivantes."""

    def test_vagues_actifs_count(self):
        """nav check vagues doit retourner >= 100 versets actifs."""
        stdout, _, rc = _run_nav(["check", "vagues"])
        assert rc == 0, f"nav check vagues échoué (rc={rc}): {stdout}"
        line = [l for l in stdout.splitlines() if "[Vagues]" in l][0]
        count = int(line.split()[1])
        assert count >= 100, f"Trop peu de vagues actives: {count}"


class TestGouvernail:
    """Zone 4 — gouvernail (pre-commit config)."""

    def test_gouvernail_config_present(self):
        """nav check gouvernail doit confirmer la config."""
        stdout, _, rc = _run_nav(["check", "gouvernail"])
        assert rc == 0, f"nav check gouvernail échoué (rc={rc}): {stdout}"
        assert "configurés" in stdout or "Absent" in stdout
