"""Validation manuelle des runners d�finis dans runners.yaml.

Usage:
    python scripts/validate_runners.py [--runner <name>] [--start] [--stop]

Sans --start : validation statique uniquement (chemins, fichiers).
Avec --start : d�marre chaque runner valide et v�rifie le health-check.
Avec --stop : arr�te les runners d�marr�s par ce script.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any

# Ensure repo root is on sys.path for 'runners' package import
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import requests
import yaml

from runners.registry import load_runners_config, get_runner
from runners.base import RunnerSpec


CONFIG_PATH = REPO_ROOT / "config" / "runners.yaml"
_STARTED: dict[str, int] = {}


def _load_config() -> list[RunnerSpec]:
    if not CONFIG_PATH.exists():
        print(f"[ERROR] {CONFIG_PATH} introuvable")
        sys.exit(1)
    return load_runners_config(CONFIG_PATH)


def static_check(specs: list[RunnerSpec]) -> bool:
    ok = True
    for spec in specs:
        wd = Path(spec.working_dir)
        print(f"[CHECK] {spec.name} ({spec.runner_type})")
        if not wd.exists():
            print(f"  [FAIL] working_dir manquant: {wd}")
            ok = False
            continue
        if spec.runner_type == "python" and spec.entrypoint:
            ep = wd / spec.entrypoint
            if not ep.exists():
                print(f"  [FAIL] entrypoint manquant: {ep}")
                ok = False
            else:
                print(f"  [OK] entrypoint: {ep}")
        elif spec.runner_type == "zig-binary" and spec.binary:
            bp = wd / spec.binary
            if not bp.exists():
                print(f"  [FAIL] binary manquant: {bp}")
                ok = False
            else:
                print(f"  [OK] binary: {bp}")
        elif spec.runner_type == "gateway-exe" and spec.command:
            print(f"  [OK] command: {' '.join(spec.command)}")
        if spec.build and spec.build.get("pre_start"):
            print(f"  [INFO] build pre_start: {spec.build.get('command')}")
        print(f"  [OK] port={spec.port} health={spec.health_path}")
    return ok


def start_runners(specs: list[RunnerSpec]) -> bool:
    ok = True
    for spec in specs:
        if spec.bootstrap:
            print(f"[SKIP] {spec.name} (bootstrap=true, d�marr� manuellement)")
            continue
        instance = get_runner(spec)
        print(f"[START] {spec.name}")
        result = instance.start()
        if result.get("status") == "error":
            print(f"  [FAIL] {result.get('detail')}")
            ok = False
            continue
        pid = result.get("pid")
        print(f"  [OK] pid={pid}")
        _STARTED[spec.name] = pid
        time.sleep(0.5)
        health = instance.health()
        if health.get("status") == "ok":
            print(f"  [OK] health-check pass�")
        else:
            print(f"  [WARN] health-check: {health}")
    return ok


def stop_runners(specs: list[RunnerSpec]) -> None:
    for spec in specs:
        pid = _STARTED.get(spec.name)
        if not pid:
            continue
        instance = get_runner(spec)
        print(f"[STOP] {spec.name} (pid={pid})")
        result = instance.stop(pid)
        print(f"  {result.get('status')}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Valide les runners KIX")
    parser.add_argument("--runner", help="Valider un runner sp�cifique")
    parser.add_argument("--start", action="store_true", help="D�marrer les runners valides")
    parser.add_argument("--stop", action="store_true", help="Arr�ter les runners d�marr�s")
    args = parser.parse_args()

    specs = _load_config()
    if args.runner:
        specs = [s for s in specs if s.name == args.runner]
        if not specs:
            print(f"[ERROR] runner inconnu: {args.runner}")
            return 1

    if args.stop:
        stop_runners(specs)
        return 0

    if not static_check(specs):
        return 1

    if args.start:
        if not start_runners(specs):
            return 1
        print("\n[INFO] runners d�marr�s. Utilisez --stop pour les arr�ter.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
