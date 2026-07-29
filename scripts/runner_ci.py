#!/usr/bin/env python3
"""
Sovereign CI Pipeline for Cognitive Runners via KIX
Orchestrates all cognitive runners (RLM, TLM, LLM, TEMPORAL) 
with dynamic CPU-aware parallelization.

Usage:
    python -m KIX.scripts.runner_ci
    python -m KIX.scripts.runner_ci --layers RLM,TLM
    python -m KIX.scripts.runner_ci --dry-run
"""

from __future__ import annotations

import argparse
import os
import sys
import time
import urllib.request
import urllib.error
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Import cognitive runners registry
from scripts.cognitive_runners import (
    get_all_runners,
    get_existing_runners,
    get_runners_by_layers,
    get_layers,
    LAYER_ORDER,
    CognitiveRunner,
)


KIX_PORT = 8800
ROOT = Path(__file__).resolve().parent.parent.parent  # L2-PLATFORM


@dataclass
class RunnerResult:
    """Result of starting a single runner."""
    name: str
    port: int
    success: bool
    error: Optional[str] = None
    pid: Optional[int] = None


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


def calculate_optimal_workers(runner_count: int) -> int:
    """
    Calculate optimal worker count for CPU-aware parallelization.
    
    Formula: min(runner_count, cpu_cores - 1)
    Reserve 1 core for KIX orchestrator + system.
    """
    cpu_cores = os.cpu_count() or 1
    max_workers = max(1, min(runner_count, cpu_cores - 1))
    return max_workers


def start_runner(runner: CognitiveRunner) -> RunnerResult:
    """Start a single cognitive runner via its src/app.py."""
    runner_dir = ROOT / runner.path_suffix
    
    if not runner_dir.exists():
        return RunnerResult(
            name=runner.name,
            port=runner.port,
            success=False,
            error=f"Directory not found: {runner_dir}"
        )
    
    app_path = runner_dir / "src" / "app.py"
    if not app_path.exists():
        return RunnerResult(
            name=runner.name,
            port=runner.port,
            success=False,
            error=f"app.py not found: {app_path}"
        )
    
    try:
        proc = subprocess.Popen(
            [sys.executable, str(app_path)],
            cwd=runner_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        
        # Wait for health check
        if wait_for_port(runner.port):
            return RunnerResult(
                name=runner.name,
                port=runner.port,
                success=True,
                pid=proc.pid
            )
        else:
            proc.terminate()
            return RunnerResult(
                name=runner.name,
                port=runner.port,
                success=False,
                error="Health check timeout"
            )
    except Exception as e:
        return RunnerResult(
            name=runner.name,
            port=runner.port,
            success=False,
            error=str(e)
        )


def start_runners_parallel(
    runners: list[CognitiveRunner],
    max_workers: int
) -> list[RunnerResult]:
    """Start multiple runners in parallel with controlled concurrency."""
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_runner = {
            executor.submit(start_runner, runner): runner 
            for runner in runners
        }
        
        for future in as_completed(future_to_runner):
            results.append(future.result())
    
    return results


def start_kix() -> Optional[subprocess.Popen]:
    """Start KIX orchestrator."""
    kix_dir = ROOT / "KIX"
    if not kix_dir.exists():
        print(f"[KIX-CI] ERROR: KIX directory not found: {kix_dir}")
        return None
    
    print("[KIX-CI] Starting KIX orchestrator on port 8800...")
    proc = subprocess.Popen(
        [sys.executable, "src/app.py"],
        cwd=kix_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    
    if wait_for_port(KIX_PORT):
        print("[KIX-CI] KIX orchestrator online")
        return proc
    else:
        print("[KIX-CI] ERROR: KIX failed to start")
        proc.terminate()
        return None


def run_probe_audit() -> bool:
    """Run KIX probe audit to verify all runners."""
    try:
        urllib.request.urlopen(f"http://localhost:{KIX_PORT}/probe/audit", timeout=10)
        print("[KIX-CI] Probe audit completed via KIX")
        return True
    except Exception as e:
        print(f"[KIX-CI] Probe audit error: {e}")
        return False


def print_summary(results: list[RunnerResult]) -> int:
    """Print CI summary and return exit code."""
    success_count = sum(1 for r in results if r.success)
    total_count = len(results)
    
    print("\n" + "=" * 60)
    print("[KIX-CI] SOVEREIGN CI PIPELINE SUMMARY")
    print("=" * 60)
    print(f"Total runners: {total_count}")
    print(f"Successful:    {success_count}")
    print(f"Failed:        {total_count - success_count}")
    print("-" * 60)
    
    for r in results:
        status = "✅ OK" if r.success else "❌ FAIL"
        pid_info = f" (PID: {r.pid})" if r.pid else ""
        err_info = f" — {r.error}" if r.error else ""
        print(f"  {status} {r.name}:{r.port}{pid_info}{err_info}")
    
    print("=" * 60)
    
    return 0 if success_count == total_count else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Sovereign CI Pipeline for Cognitive Runners")
    parser.add_argument(
        "--layers", 
        default="all",
        help=f"Comma-separated layers to test: {', '.join(get_layers())} (default: all)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List runners that would be tested without starting them"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=0,
        help="Override worker count (0 = auto)"
    )
    parser.add_argument(
        "--no-kix",
        action="store_true",
        help="Skip KIX orchestrator (assume already running)"
    )
    args = parser.parse_args()
    
    print("[KIX-CI] Sovereign CI Pipeline starting...")
    print(f"[KIX-CI] Root: {ROOT}")
    print(f"[KIX-CI] CPU cores: {os.cpu_count()}")
    
    # Resolve runners
    if args.layers == "all":
        runners = list(get_all_runners())
    else:
        layer_list = [l.strip() for l in args.layers.split(",")]
        runners = list(get_runners_by_layers(layer_list))
    
    # Filter to existing directories
    existing_runners = get_existing_runners(str(ROOT))
    runner_names = {r.name for r in existing_runners}
    runners = [r for r in runners if r.name in runner_names]
    
    if not runners:
        print("[KIX-CI] No matching runners found")
        return 1
    
    print(f"[KIX-CI] Target runners ({len(runners)}):")
    for r in runners:
        print(f"  - {r.name} ({r.layer}) port {r.port}")
    
    if args.dry_run:
        print("[KIX-CI] Dry run complete — no runners started")
        return 0
    
    # Calculate workers
    worker_count = args.workers if args.workers > 0 else calculate_optimal_workers(len(runners))
    print(f"[KIX-CI] Parallel workers: {worker_count}")
    
    # Start KIX if not skipped
    kix_proc = None
    if not args.no_kix:
        kix_proc = start_kix()
        if not kix_proc:
            return 1
    
    try:
        # Start runners in parallel
        print(f"[KIX-CI] Starting {len(runners)} runners...")
        start_time = time.time()
        results = start_runners_parallel(runners, worker_count)
        elapsed = time.time() - start_time
        
        print(f"[KIX-CI] All runners started in {elapsed:.1f}s")
        
        # Run probe audit
        if not args.no_kix:
            run_probe_audit()
        
        # Print summary and return exit code
        return print_summary(results)
    
    finally:
        if kix_proc:
            print("[KIX-CI] Stopping KIX orchestrator...")
            kix_proc.terminate()


if __name__ == "__main__":
    sys.exit(main())