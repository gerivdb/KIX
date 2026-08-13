"""Tests for KIX-IMMUNE V21.0 module."""

import mmap
import os
import struct
import sys
import time
from pathlib import Path

import pytest

# Add KIX src to path
REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from kix.immune import (
    KORXStateKernel,
    SOMA,
    BernsteinG1,
    compute_blake3,
    validate_heartbeat,
    validate_timx_token,
    STATE_KBIN_SIZE,
    HEADER_MAGIC,
    MAX_GIT_PROCESSES,
)


class TestKORXStateKernel:
    def test_kbin_size(self):
        assert STATE_KBIN_SIZE == 372

    def test_create_state_kbin(self):
        kernel = KORXStateKernel()
        assert kernel.path.exists()
        assert kernel.path.stat().st_size == STATE_KBIN_SIZE

    def test_read_write_wal_seq(self):
        kernel = KORXStateKernel()
        kernel.write_wal_seq(42)
        assert kernel.read_wal_seq() == 42

    def test_read_write_phi_cps(self):
        kernel = KORXStateKernel()
        kernel.write_phi_cps(3.14)
        assert abs(kernel.read_phi_cps() - 3.14) < 0.001

    def test_runner_bitmask(self):
        kernel = KORXStateKernel()
        bitmask = bytes([0xFF] * 256)
        kernel.write_runner_bitmask(bitmask)
        assert kernel.read_runner_bitmask() == bitmask

    def test_mmap_recovery(self):
        kernel = KORXStateKernel()
        kernel.write_wal_seq(123)
        kernel2 = KORXStateKernel()
        assert kernel2.read_wal_seq() == 123

    def test_git_count(self):
        kernel = KORXStateKernel()
        kernel.write_git_count(2)
        assert kernel.read_git_count() == 2

    def test_git_count_max(self):
        kernel = KORXStateKernel()
        kernel.write_git_count(999)
        assert kernel.read_git_count() <= MAX_GIT_PROCESSES

    def test_git_pids(self):
        kernel = KORXStateKernel()
        pids = [1234, 5678, 9012, 3456]
        kernel.write_git_pids(pids)
        assert kernel.read_git_pids() == pids

    def test_can_spawn_git(self):
        kernel = KORXStateKernel()
        kernel.write_git_count(0)
        assert kernel.can_spawn_git() is True
        kernel.write_git_count(MAX_GIT_PROCESSES)
        assert kernel.can_spawn_git() is False

    def test_register_git_process(self):
        kernel = KORXStateKernel()
        kernel.write_git_count(0)
        kernel.write_git_pids([0, 0, 0, 0])
        assert kernel.register_git_process(1111) is True
        assert kernel.read_git_count() == 1
        assert kernel.register_git_process(2222) is True
        assert kernel.read_git_count() == 2

    def test_unregister_git_process(self):
        kernel = KORXStateKernel()
        kernel.write_git_count(2)
        kernel.write_git_pids([1111, 2222, 0, 0])
        kernel.unregister_git_process(1111)
        assert kernel.read_git_count() == 1


class TestTINAHeartbeat:
    def test_blake3_deterministic(self):
        data = b"test data"
        h1 = compute_blake3(data)
        h2 = compute_blake3(data)
        assert h1 == h2

    def test_blake3_different_inputs(self):
        h1 = compute_blake3(b"data1")
        h2 = compute_blake3(b"data2")
        assert h1 != h2

    def test_validate_heartbeat_ok(self):
        data = b"registry"
        expected = compute_blake3(data)
        assert validate_heartbeat(data, expected, timeout_ms=15) is True

    def test_validate_heartbeat_mismatch(self):
        data = b"registry"
        wrong_hash = b"\x00" * 16
        assert validate_heartbeat(data, wrong_hash, timeout_ms=15) is False


class TestTIMXToken:
    def test_valid_token(self):
        assert validate_timx_token(100, 200, delta_max=100) is True

    def test_expired_token(self):
        assert validate_timx_token(100, 202, delta_max=100) is False

    def test_zero_delta(self):
        assert validate_timx_token(100, 100, delta_max=100) is True


class TestSOMA:
    def test_check_status_returns_dict(self):
        soma = SOMA()
        status = soma.check_status()
        assert "mode" in status
        assert "ram_usage" in status

    def test_mode_normal(self):
        soma = SOMA()
        status = soma.check_status()
        assert status["mode"] in ("NORMAL", "LOW_FREQUENCY", "CRITICAL")


class TestBernsteinG1:
    def test_no_cycle(self):
        bg = BernsteinG1()
        edges = [("A", "B"), ("B", "C")]
        assert bg.detect_cycle(edges) is False

    def test_cycle_detected(self):
        bg = BernsteinG1()
        edges = [("A", "B"), ("B", "C"), ("C", "A")]
        assert bg.detect_cycle(edges) is True

    def test_phi_cps_drop_on_cycle(self):
        bg = BernsteinG1()
        bg.phi_cps = 4.559
        bg.update_phi_cps(has_cycle=True)
        assert bg.phi_cps == 1.000

    def test_phi_cps_recovery(self):
        bg = BernsteinG1()
        bg.phi_cps = 1.000
        bg.update_phi_cps(has_cycle=False)
        assert bg.phi_cps > 1.000
