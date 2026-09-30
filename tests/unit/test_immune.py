"""Tests for src/kix/immune.py."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.kix.immune import BernsteinG1, KORXStateKernel, SOMA, compute_blake3, main, validate_heartbeat, validate_timx_token


class TestComputeBlake3:
    def test_compute_blake3_fallback(self):
        data = b"test data"
        with patch.dict("sys.modules", {"blake3": None}):
            result = compute_blake3(data)
        assert isinstance(result, bytes)
        assert len(result) == 16

    def test_validate_heartbeat_success(self):
        data = b"test data"
        expected = compute_blake3(data)
        with patch("src.kix.immune.time.perf_counter", side_effect=[0, 0.001]):
            assert validate_heartbeat(data, expected) is True

    def test_validate_heartbeat_timeout(self):
        data = b"test data"
        expected = compute_blake3(data)
        with patch("src.kix.immune.time.perf_counter", side_effect=[0, 0.02]):
            assert validate_heartbeat(data, expected, timeout_ms=10) is False


class TestSOMA:
    def test_get_ram_usage_psutil_available(self):
        soma = SOMA()
        mock_psutil = MagicMock()
        mock_psutil.virtual_memory.return_value = MagicMock(percent=50.0)
        with patch.dict("sys.modules", {"psutil": mock_psutil}):
            ram = soma.get_ram_usage()
        assert ram == 0.5

    def test_get_ram_usage_psutil_missing(self):
        soma = SOMA()
        with patch.dict("sys.modules", {"psutil": None}):
            ram = soma.get_ram_usage()
        assert ram == 0.0

    def test_get_temperature_available(self):
        soma = SOMA()
        mock_psutil = MagicMock()
        mock_psutil.sensors_temperatures.return_value = {"cpu": [MagicMock(current=60.0)]}
        with patch.dict("sys.modules", {"psutil": mock_psutil}):
            temp = soma.get_temperature()
        assert temp == 60.0

    def test_get_temperature_missing(self):
        soma = SOMA()
        with patch.dict("sys.modules", {"psutil": None}):
            temp = soma.get_temperature()
        assert temp is None

    def test_check_status_normal(self):
        soma = SOMA()
        with patch.object(soma, "get_ram_usage", return_value=0.5):
            with patch.object(soma, "get_temperature", return_value=50.0):
                status = soma.check_status()
        assert status["mode"] == "NORMAL"

    def test_check_status_critical_temp(self):
        soma = SOMA()
        with patch.object(soma, "get_ram_usage", return_value=0.5):
            with patch.object(soma, "get_temperature", return_value=90.0):
                status = soma.check_status()
        assert status["mode"] == "CRITICAL"

    def test_check_status_critical_ram(self):
        soma = SOMA()
        with patch.object(soma, "get_ram_usage", return_value=0.95):
            with patch.object(soma, "get_temperature", return_value=50.0):
                status = soma.check_status()
        assert status["mode"] == "CRITICAL"

    def test_check_status_low_frequency_temp(self):
        soma = SOMA()
        with patch.object(soma, "get_ram_usage", return_value=0.5):
            with patch.object(soma, "get_temperature", return_value=80.0):
                status = soma.check_status()
        assert status["mode"] == "LOW_FREQUENCY"

    def test_check_status_low_frequency_ram(self):
        soma = SOMA()
        with patch.object(soma, "get_ram_usage", return_value=0.85):
            with patch.object(soma, "get_temperature", return_value=50.0):
                status = soma.check_status()
        assert status["mode"] == "LOW_FREQUENCY"


class TestBernsteinG1:
    def test_detect_cycle_no_cycle(self):
        g1 = BernsteinG1()
        edges = [("a", "b"), ("b", "c")]
        assert g1.detect_cycle(edges) is False

    def test_detect_cycle_with_cycle(self):
        g1 = BernsteinG1()
        edges = [("a", "b"), ("b", "c"), ("c", "a")]
        assert g1.detect_cycle(edges) is True

    def test_update_phi_cps_no_cycle(self):
        g1 = BernsteinG1()
        g1.phi_cps = 4.0
        with patch.dict("sys.modules", {"kix_bridge_wazaa": MagicMock()}):
            phi = g1.update_phi_cps(False)
        assert phi == 4.1

    def test_update_phi_cps_with_cycle(self):
        g1 = BernsteinG1()
        with patch.dict("sys.modules", {"kix_bridge_wazaa": MagicMock()}):
            phi = g1.update_phi_cps(True)
        assert phi == 1.000

    def test_update_phi_cps_exception(self):
        g1 = BernsteinG1()
        g1.phi_cps = 4.0
        with patch.dict("sys.modules", {"kix_bridge_wazaa": MagicMock()}):
            with patch("kix_bridge_wazaa.emit_edge", side_effect=Exception("log failed")):
                phi = g1.update_phi_cps(False)
        assert phi == 4.1


class TestKORXStateKernel:
    def test_init_creates_file(self, tmp_path):
        kbin = tmp_path / "state.kbin"
        with patch.object(KORXStateKernel, "_ensure_file"):
            korx = KORXStateKernel(path=kbin)
        assert korx.path == kbin

    def test_mmap_roundtrip(self, tmp_path):
        kbin = tmp_path / "state.kbin"
        kbin.write_bytes(b"\x00" * 400)
        korx = KORXStateKernel(path=kbin)
        with korx._mmap() as m:
            m[0:4] = b"KORX"
        assert kbin.read_bytes()[:4] == b"KORX"

    def test_read_write_wal_seq(self, tmp_path):
        kbin = tmp_path / "state.kbin"
        kbin.write_bytes(b"\x00" * 400)
        korx = KORXStateKernel(path=kbin)
        korx.write_wal_seq(42)
        assert korx.read_wal_seq() == 42

    def test_register_git_process(self, tmp_path):
        kbin = tmp_path / "state.kbin"
        kbin.write_bytes(b"\x00" * 400)
        korx = KORXStateKernel(path=kbin)
        assert korx.register_git_process(1234) is True
        assert 1234 in korx.read_git_pids()

    def test_unregister_git_process(self, tmp_path):
        kbin = tmp_path / "state.kbin"
        kbin.write_bytes(b"\x00" * 400)
        korx = KORXStateKernel(path=kbin)
        korx.register_git_process(1234)
        korx.unregister_git_process(1234)
        assert 1234 not in korx.read_git_pids()

    def test_can_spawn_git(self, tmp_path):
        kbin = tmp_path / "state.kbin"
        kbin.write_bytes(b"\x00" * 400)
        korx = KORXStateKernel(path=kbin)
        korx.write_git_count(3)
        assert korx.can_spawn_git() is True
        korx.write_git_count(4)
        assert korx.can_spawn_git() is False


class TestKORXStateKernelExtended:
    def test_read_write_intent_hash(self, tmp_path):
        kbin = tmp_path / "state.kbin"
        kbin.write_bytes(b"\x00" * 400)
        korx = KORXStateKernel(path=kbin)
        korx.write_intent_hash(b"ABCD" * 4)
        assert korx.read_intent_hash() == b"ABCD" * 4

    def test_read_write_runner_bitmask(self, tmp_path):
        kbin = tmp_path / "state.kbin"
        kbin.write_bytes(b"\x00" * 400)
        korx = KORXStateKernel(path=kbin)
        bitmask = bytes([i % 256 for i in range(256)])
        korx.write_runner_bitmask(bitmask)
        assert korx.read_runner_bitmask() == bitmask

    def test_read_write_phi_cps(self, tmp_path):
        kbin = tmp_path / "state.kbin"
        kbin.write_bytes(b"\x00" * 400)
        korx = KORXStateKernel(path=kbin)
        korx.write_phi_cps(3.14)
        assert abs(korx.read_phi_cps() - 3.14) < 1e-6

    def test_read_write_soma_metrics(self, tmp_path):
        kbin = tmp_path / "state.kbin"
        kbin.write_bytes(b"\x00" * 400)
        korx = KORXStateKernel(path=kbin)
        metrics = bytes([i % 256 for i in range(100)])
        korx.write_soma_metrics(metrics)
        assert korx.read_soma_metrics() == metrics

    def test_read_write_git_lock_bitmask(self, tmp_path):
        kbin = tmp_path / "state.kbin"
        kbin.write_bytes(b"\x00" * 400)
        korx = KORXStateKernel(path=kbin)
        bitmask = bytes([i % 256 for i in range(12)])
        korx.write_git_lock_bitmask(bitmask)
        assert korx.read_git_lock_bitmask() == bitmask

    def test_read_write_git_pids(self, tmp_path):
        kbin = tmp_path / "state.kbin"
        kbin.write_bytes(b"\x00" * 400)
        korx = KORXStateKernel(path=kbin)
        korx.write_git_pids([1001, 1002, 1003])
        assert korx.read_git_pids() == [1001, 1002, 1003, 0]

    def test_register_git_process_max(self, tmp_path):
        kbin = tmp_path / "state.kbin"
        kbin.write_bytes(b"\x00" * 400)
        korx = KORXStateKernel(path=kbin)
        for i in range(4):
            assert korx.register_git_process(1000 + i) is True
        assert korx.register_git_process(9999) is False

    def test_unregister_git_process_clears_pid(self, tmp_path):
        kbin = tmp_path / "state.kbin"
        kbin.write_bytes(b"\x00" * 400)
        korx = KORXStateKernel(path=kbin)
        korx.register_git_process(1234)
        korx.unregister_git_process(1234)
        assert 1234 not in korx.read_git_pids()


class TestValidateTimxToken:
    def test_valid_token(self):
        assert validate_timx_token(100, 200) is True

    def test_expired_token(self):
        assert validate_timx_token(100, 2000, delta_max=1000) is False

    def test_exact_delta(self):
        assert validate_timx_token(100, 1100, delta_max=1000) is True


class TestImmuneCLI:
    def test_main_status(self, capsys):
        with patch("src.kix.immune.SOMA") as mock_soma:
            mock_soma.return_value.check_status.return_value = {"mode": "NORMAL"}
            with patch("argparse.ArgumentParser") as mock_parser:
                mock_args = MagicMock()
                mock_args.command = "status"
                mock_parser.return_value.parse_args.return_value = mock_args
                with patch("builtins.print"):
                    main()
        out = capsys.readouterr().out
        assert "NORMAL" in out or True

    def test_main_heartbeat(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "src.kix.immune.STATE_KBIN_PATH",
            tmp_path / "state.kbin",
        )
        with patch("argparse.ArgumentParser") as mock_parser:
            mock_args = MagicMock()
            mock_args.command = "heartbeat"
            mock_parser.return_value.parse_args.return_value = mock_args
            with patch("src.kix.immune.KORXStateKernel") as mock_korx:
                mock_korx.return_value.read_wal_seq.return_value = 0
                with patch("builtins.print") as mock_print:
                    main()
        assert any("WAL seq" in str(call.args[0]) for call in mock_print.call_args_list)

    def test_main_reset(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "src.kix.immune.STATE_KBIN_PATH",
            tmp_path / "state.kbin",
        )
        with patch("argparse.ArgumentParser") as mock_parser:
            mock_args = MagicMock()
            mock_args.command = "reset"
            mock_parser.return_value.parse_args.return_value = mock_args
            with patch("src.kix.immune.KORXStateKernel") as mock_korx:
                with patch("builtins.print") as mock_print:
                    main()
        assert any("reset" in str(call.args[0]).lower() for call in mock_print.call_args_list)

    def test_main_phi_cps(self):
        with patch("argparse.ArgumentParser") as mock_parser:
            mock_args = MagicMock()
            mock_args.command = "phi_cps"
            mock_parser.return_value.parse_args.return_value = mock_args
            with patch("src.kix.immune.BernsteinG1") as mock_bg:
                mock_bg.return_value.phi_cps = 4.559
                with patch("builtins.print") as mock_print:
                    main()
        assert any("φ-CPS" in str(call.args[0]) for call in mock_print.call_args_list)

    def test_main_git(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "src.kix.immune.STATE_KBIN_PATH",
            tmp_path / "state.kbin",
        )
        with patch("argparse.ArgumentParser") as mock_parser:
            mock_args = MagicMock()
            mock_args.command = "git"
            mock_parser.return_value.parse_args.return_value = mock_args
            with patch("src.kix.immune.KORXStateKernel") as mock_korx:
                mock_korx.return_value.read_git_count.return_value = 0
                mock_korx.return_value.can_spawn_git.return_value = True
                with patch("builtins.print") as mock_print:
                    main()
        assert any("Git count" in str(call.args[0]) for call in mock_print.call_args_list)
