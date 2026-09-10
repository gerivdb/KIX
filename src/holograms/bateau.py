#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Holographe Bateau — Template métrique VERSES (PRD-MOC-027 §3.2)
IntentHash: 0xHOLOGRAPHE_BATEAU_20260910

Transposition holographique bateau → n'importe quel repo.
Usage : python holographe_bateau.py --repo <path> --zone <name>
Output : JSON hologramme bateau {coque, vagues, gouvernail, vigie, ancre, equipage, pilote}
"""
import io
import sys
import argparse
import json
from pathlib import Path

# ERR_030 FIX — UTF-8 wrapper
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def holographe_bateau(repo_path: Path) -> dict:
    """Génère l'hologramme bateau pour un repo."""
    repo = Path(repo_path)
    if not repo.exists():
        return {"error": f"Repo not found: {repo}", "hologramme": None}

    return {
        "coque": _scan_coque(repo),
        "vagues": _scan_vagues(repo),
        "gouvernail": _scan_gouvernail(repo),
        "vigie": _scan_vigie(repo),
        "ancre": _scan_ancre(repo),
        "equipage": _scan_equipage(repo),
        "pilote": _scan_pilote(repo),
    }


def _scan_coque(repo: Path) -> dict:
    """Coque = MANIFEST.yaml / registre."""
    candidates = ["MANIFEST.yaml", "manifest.yaml", "package.json", "pyproject.toml"]
    for c in candidates:
        f = repo / c
        if f.exists():
            content = f.read_text(encoding="utf-8") if f.stat().st_size < 1_000_000 else "binary"
            return {
                "type": "registre",
                "source": str(f),
                "size": f.stat().st_size,
                "lines": content.count("\n") if isinstance(content, str) else 0,
            }
    return {"type": "registre", "source": None, "found": False}


def _scan_vagues(repo: Path) -> dict:
    """Vagues = fichiers actifs."""
    src_dirs = ["src", "scripts", "lib", "kix/bin"]
    total = 0
    for d in src_dirs:
        src = repo / d
        if src.exists():
            total += sum(1 for _ in src.rglob("*.py"))
    return {"type": "fichiers_actifs", "count": total, "dirs": src_dirs}


def _scan_gouvernail(repo: Path) -> dict:
    """Gouvernail = tests/validation."""
    test_dirs = ["tests", "test", "spec", "__tests__"]
    has_tests = any((repo / d).exists() for d in test_dirs)
    return {"type": "validation", "tests_dir": has_tests, "dirs": test_dirs}


def _scan_vigie(repo: Path) -> dict:
    """Vigie = coverage/design_seeker."""
    seekers = ["design_seeker.py", "coverage.json", "cobertura.xml"]
    found = [str(repo / s) for s in seekers if (repo / s).exists()]
    return {"type": "observation", "seekers_found": found}


def _scan_ancre(repo: Path) -> dict:
    """Ancre = archive/WAL."""
    archives = ["archive", "migrated", "wal", "REPORTS"]
    wal_files = list(repo.glob("*.jsonl")) + list(repo.glob("**/*.wal"))
    return {"type": "historique", "wal_files": len(wal_files), "dirs": archives}


def _scan_equipage(repo: Path) -> dict:
    """Equipage = agents/experts."""
    agents = ["agents", "citizen", "skills", "DEV-VERSE"]
    found = [str(repo / d) for d in agents if (repo / d).exists()]
    return {"type": "experts", "dirs_found": found}


def _scan_pilote(repo: Path) -> dict:
    """Pilote = audit/scripts."""
    pilots = ["audit", "scripts", "bin", "run.py", "main.py"]
    found = [str(repo / p) for p in pilots if (repo / p).exists()]
    return {"type": "navigation", "scripts_found": found}


def main():
    parser = argparse.ArgumentParser(description="Holographe Bateau — Template VERSES")
    parser.add_argument("--repo", required=True, help="Repo path (ex: D:/DO/WEB/TOOLS/.../REPO)")
    parser.add_argument("--zone", default="all", help="Zone to scan: coque|vagues|gouvernail|vigie|ancre|equipage|pilote|all")
    args = parser.parse_args()

    repo = Path(args.repo)
    hologramme = holographe_bateau(repo)

    if args.zone != "all":
        result = hologramme.get(args.zone)
    else:
        result = hologramme

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
