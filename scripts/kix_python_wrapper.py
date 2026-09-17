#!/usr/bin/env python3
"""Wrapper pour exécuter les modules KG-L tools depuis le hook pre-commit.

Ajoute `src` au PYTHONPATH pour que `python -m kix.tools.*` fonctionne
depuis la racine du repo KIX.

IntentHash: 0xPRD_MOC_VOLTX_PHASE2_KG_L_ENGINE_20260905
"""

from __future__ import annotations

import sys
from pathlib import Path

KIX_ROOT = Path(__file__).resolve().parent.parent
SRC = KIX_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

if __name__ == "__main__":
    # Usage: python scripts/kix_python_wrapper.py <module_path>
    # Exemple: python scripts/kix_python_wrapper.py kix.tools.validate_designs --scope kg-l
    if len(sys.argv) < 2:
        print("Usage: kix_python_wrapper.py <module> [args...]")
        sys.exit(1)
    module = sys.argv[1]
    args = sys.argv[2:]
    sys.argv = [module] + args
    try:
        __import__(module)
        if "." in module:
            module_path, func_name = module.rsplit(".", 1)
            mod = __import__(module_path, fromlist=[func_name])
            func = getattr(mod, func_name)
            sys.exit(func(*args))
    except Exception as exc:
        print(f"[kix_python_wrapper] ERROR: {exc}")
        sys.exit(1)
