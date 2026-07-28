# Sovereign CI Pipeline for RLM Services via KIX
# Orchestrates all RLM runners and runs their test suites
# Dynamically scales to available CPU cores for maximum elegance

from __future__ import annotations

import os
import sys
import time
import urllib.request
import urllib.error
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Optional


@dataclass
class RunnerConfig:
    """Configuration for a single RLM runner"""
    name: str
    port: int
    path: str


# Dynamically configure runners from known repositories
# Each runner: (name, port, relative_path_from_L2_PLATFORM)
RUNNER_DEFINITIONS = [
    ("RLM-SECURE", 8797, "RLM-SECURE"),
    ("RLM-DEPLOY", 8795, "RLM-DEPLOY"),
    ("RLM-GRAPH", 8794, "RLM-GRAPH"),
    ("RLM-CONFIG", 8793, "RLM-CONFIG"),
    ("RLM-INCIDENT", 8798, "RLM-INCIDENT"),
    ("RLM-RELEASE", 8799, "RLM-RELEASE"),
]


def get_optimal_worker_count() -> int:
    """
    Dynamically determine optimal worker count based on CPU cores.
    Returns max workers for ThreadPoolExecutor, reserving 1 core for system.
    """
    cpu_count = os.cpu_count() or 1
    # Reserve 1 core for system/KIX, use rest for parallel runner startup
    # Minimum 1 worker, maximum = cpu_count - 1 (or 1 if only 1 core)
    return max(1, cpu_count - 1)


def build_runner_configs(root: Path) -> list[RunnerConfig]:
    """Build runner configs from definitions, only including existing directories."""
    configs = []
    for name, port, rel_path in RUNNER_DEFINITIONS:
        runner_path = root / rel_path
        if runner_path.exists():
            configs.append(RunnerConfig(name=name, port=port, path=str(runner_path)))
        else:
            print(f"[KIX-CI] SKIP {name}: directory not found at {runner_path}")
    return configs


def wait_for_port(port: int, timeout: float = 5.0) -> bool:
    """Wait for service to respond on /healthz."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            urllib.request.urlopen(f"http://localhost:{port}/healthz", timeout=1.0)
            return True
        except (urllib.error.URLError, ConnectionRefusedError):
            time.sleep(0.3)
    return False


def start_runner(config: RunnerConfig) -> tuple[str, bool, Optional[subprocess.Popen]]:
    """Start a single runner and verify it's healthy. Returns (name, success, process)."""
    try:
        proc = subprocess.Popen(
            [sys.executable, "src/app.py"],
            cwd=config.path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        healthy = wait_for_port(config.port)
        return (config.name, healthy, proc if healthy else None)
    except Exception as e:
        print(f"[KIX-CI] {config.name}: FAILED to start - {e}")
        return (config.name, False, None)


def run_probe_audit(kix_port: int) -> bool:
    """Run probe audit via KIX orchestrator."""
    try:
        urllib.request.urlopen(f"http://localhost:{kix_port}/probe/audit", timeout=10)
        return True
    except Exception as e:
        print(f"[KIX-CI] Probe audit error: {e}")
        return False


def main() -> int:
    print("[KIX-CI] Sovereign pipeline starting...")

    # Detect optimal worker count based on CPU cores
    optimal_workers = get_optimal_worker_count()
    print(f"[KIX-CI] Detected {os.cpu_count()} CPU cores, using {optimal_workers} parallel workers")

    # Build runner configurations from existing directories
    root = Path(__file__).resolve().parent.parent.parent  # L2-PLATFORM
    runner_configs = build_runner_configs(root)

    if not runner_configs:
        print("[KIX-CI] No runners found to test")
        return 1

    print(f"[KIX-CI] Found {len(runner_configs)} runners to test")

    # Start KIX orchestrator first
    kix_proc = subprocess.Popen(
        [sys.executable, "src/app.py"],
        cwd=root / "KIX",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    kix_port = 8800
    if not wait_for_port(kix_port):
        print("[KIX-CI] ERROR: KIX failed to start")
        kix_proc.terminate()
        return 1

    print("[KIX-CI] KIX online")

    # Start runners in parallel using optimal worker count
    failed = []
    running_procs = []

    with ThreadPoolExecutor(max_workers=optimal_workers) as executor:
        future_to_config = {
            executor.submit(start_runner, config): config
            for config in runner_configs
        }

        for future in as_completed(future_to_config):
            name, healthy, proc = future.result()
            if healthy:
                print(f"[KIX-CI] {name}: OK (port {next(c.port for c in runner_configs if c.name == name)})")
                running_procs.append(proc)
            else:
                print(f"[KIX-CI] {name}: FAILED to start")
                failed.append(name)

    # Run probe audit via KIX
    print("[KIX-CI] Running probe audit via KIX...")
    audit_ok = run_probe_audit(kix_port)
    if audit_ok:
        print("[KIX-CI] Probe audit completed via KIX")
    else:
        print("[KIX-CI] Probe audit failed")

    # Cleanup all runner processes
    for proc in running_procs:
        if proc:
            proc.terminate()

    kix_proc.terminate()

    if failed:
        print(f"[KIX-CI] Failed runners: {', '.join(failed)}")
        return 1

    print("[KIX-CI] Pipeline completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())