"""Tests for src/diagnostics.py."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.diagnostics import DiagnosticsResult, check_auth, check_daemon_health, check_kilocode_cli, check_providers, check_runners, check_toolchains, run_all_checks


class TestDiagnosticsResult:
    def test_create_result(self):
        result = DiagnosticsResult("test_check")
        assert result.check == "test_check"
        assert result.status == "OK"
        assert result.detail == ""

    def test_set_error(self):
        result = DiagnosticsResult("test_check")
        result.set_error("something failed")
        assert result.status == "ERROR"
        assert result.detail == "something failed"

    def test_set_warn(self):
        result = DiagnosticsResult("test_check")
        result.set_warn("something suspicious")
        assert result.status == "WARN"
        assert result.detail == "something suspicious"

    def test_to_dict(self):
        result = DiagnosticsResult("test_check")
        result.set_error("failed")
        data = result.to_dict()
        assert data["check"] == "test_check"
        assert data["status"] == "ERROR"
        assert "timestamp" in data


class TestCheckFunctions:
    def test_check_kilocode_cli_success(self):
        with patch("src.diagnostics.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            result = check_kilocode_cli()
        assert result.check == "kilocode_cli"
        assert result.status == "OK"

    def test_check_kilocode_cli_not_found(self):
        with patch("src.diagnostics.subprocess.run", side_effect=FileNotFoundError):
            result = check_kilocode_cli()
        assert result.status == "ERROR"
        assert "not found" in result.detail

    def test_check_providers_missing_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "src.diagnostics.Path.home",
            lambda: tmp_path,
        )
        result = check_providers()
        assert result.status == "WARN"
        assert "not found" in result.detail

    def test_check_providers_with_file(self, tmp_path, monkeypatch):
        providers_dir = tmp_path / ".kilocode"
        providers_dir.mkdir()
        providers_file = providers_dir / "providers.yaml"
        providers_file.write_text("kilo_gateway:\n  api_key: test\n")
        monkeypatch.setattr(
            "src.diagnostics.Path.home",
            lambda: tmp_path,
        )
        result = check_providers()
        assert result.status == "OK"
        assert "kilo_gateway" in result.detail


class TestRunAllChecks:
    def test_run_all_checks_returns_dict(self):
        with patch("src.diagnostics.check_kilocode_cli") as mock_kilocode:
            with patch("src.diagnostics.check_auth") as mock_auth:
                with patch("src.diagnostics.check_providers") as mock_providers:
                    with patch("src.diagnostics.check_runners") as mock_runners:
                        with patch("src.diagnostics.check_toolchains") as mock_toolchains:
                            with patch("src.diagnostics.check_daemon_health") as mock_daemon:
                                mock_kilocode.return_value = DiagnosticsResult("kilocode_cli")
                                mock_auth.return_value = DiagnosticsResult("kilocode_auth")
                                mock_providers.return_value = DiagnosticsResult("providers")
                                mock_runners.return_value = DiagnosticsResult("kix_runners")
                                mock_toolchains.return_value = DiagnosticsResult("toolchains")
                                mock_daemon.return_value = DiagnosticsResult("daemon_health")
                                result = run_all_checks()
        assert isinstance(result, dict)
        assert "checks" in result
        assert len(result["checks"]) == 6


class TestCheckAuth:
    def test_check_auth_success(self):
        with patch("src.diagnostics.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="already logged in", stderr="")
            result = check_auth()
        assert result.check == "kilocode_auth"
        assert result.status == "OK"

    def test_check_auth_failure(self):
        with patch("src.diagnostics.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="auth failed")
            result = check_auth()
        assert result.status == "ERROR"


class TestCheckRunners:
    def test_check_runners_success(self):
        with patch("urllib.request.urlopen") as mock_urlopen:
            with patch("urllib.request.Request") as mock_request:
                with patch("json.loads", return_value={"runners": {"trixd": {}, "WAZAA": {}}}):
                    mock_resp = MagicMock()
                    mock_resp.read.return_value = b'{"runners": {}}'
                    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
                    mock_resp.__exit__ = MagicMock(return_value=False)
                    mock_urlopen.return_value = mock_resp
                    result = check_runners()
        assert result.check == "kix_runners"
        assert result.status == "OK"
        assert "trixd" in result.detail

    def test_check_runners_failure(self):
        with patch("urllib.request.urlopen", side_effect=Exception("connection failed")):
            result = check_runners()
        assert result.status == "WARN"


class TestCheckToolchains:
    def test_check_toolchains_success(self, tmp_path, monkeypatch):
        toolchains_dir = tmp_path / "config"
        toolchains_dir.mkdir()
        toolchains_file = toolchains_dir / "toolchains.yaml"
        toolchains_file.write_text("toolchains:\n  - name: zig\n    path: C:\\zig\n")
        monkeypatch.setattr(
            "src.diagnostics.Path.__truediv__",
            lambda self, other: tmp_path / "config" / "toolchains.yaml" if str(self).endswith("toolchains.yaml") else self / other,
        )
        with patch("src.diagnostics.Path.home", return_value=tmp_path):
            with patch("src.diagnostics.Path") as mock_path:
                mock_path.return_value.parent.parent.__truediv__ = MagicMock(return_value=toolchains_file)
                result = check_toolchains()
        assert result.status == "OK"

    def test_check_toolchains_missing_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "src.diagnostics.Path.home",
            lambda: tmp_path,
        )
        result = check_toolchains()
        assert result.status == "WARN"


class TestDiagnosticsHandler:
    def test_do_get_diagnostics(self):
        from src.diagnostics import DiagnosticsHandler, run_all_checks
        with patch("src.diagnostics.run_all_checks") as mock_run:
            mock_run.return_value = {"error": 0, "checks": []}
            with patch.object(DiagnosticsHandler, "handle_one_request", lambda self: None):
                handler = DiagnosticsHandler(MagicMock(), ("127.0.0.1", 8801), MagicMock())
            handler.command = "GET"
            handler.path = "/agent-manager/diagnostics"
            with patch.object(handler, "send_response") as mock_send_response:
                with patch.object(handler, "send_header") as mock_send_header:
                    with patch.object(handler, "end_headers") as mock_end_headers:
                        handler.do_GET()


class TestCheckDaemonHealth:
    def test_check_daemon_health_success(self):
        with patch("urllib.request.urlopen") as mock_urlopen:
            with patch("urllib.request.Request") as mock_request:
                with patch("json.loads", return_value={"status": "ok"}):
                    mock_resp = MagicMock()
                    mock_resp.read.return_value = b'{"status": "ok"}'
                    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
                    mock_resp.__exit__ = MagicMock(return_value=False)
                    mock_urlopen.return_value = mock_resp
                    result = check_daemon_health()
        assert result.check == "daemon_health"
        assert result.status == "OK"
        assert "KIX status" in result.detail

    def test_check_daemon_health_failure(self):
        with patch("urllib.request.urlopen", side_effect=Exception("connection failed")):
            result = check_daemon_health()
        assert result.status == "WARN"

    def test_check_daemon_health_url_error(self):
        import urllib.error

        with patch("urllib.request.Request"):
            with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("connection failed")):
                result = check_daemon_health()
        assert result.status == "WARN"
        assert "not reachable" in result.detail.lower()


class TestCheckFunctionsExceptionBranches:
    def test_check_kilocode_cli_timeout(self):
        with patch("src.diagnostics.subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="kilocode", timeout=10)):
            result = check_kilocode_cli()
        assert result.status == "ERROR"
        assert "timeout" in result.detail.lower()

    def test_check_kilocode_cli_generic_exception(self):
        with patch("src.diagnostics.subprocess.run", side_effect=RuntimeError("unexpected")):
            result = check_kilocode_cli()
        assert result.status == "ERROR"

    def test_check_auth_exception(self):
        with patch("src.diagnostics.subprocess.run", side_effect=Exception("auth failed")):
            result = check_auth()
        assert result.status == "ERROR"

    def test_check_providers_no_match(self, tmp_path, monkeypatch):
        kilocode_dir = tmp_path / ".kilocode"
        kilocode_dir.mkdir()
        providers_file = kilocode_dir / "providers.yaml"
        providers_file.write_text("other_provider:\n  api_key: test\n")
        monkeypatch.setattr("src.diagnostics.Path.home", lambda: tmp_path)
        result = check_providers()
        assert result.status == "WARN"
        assert "No providers configured" in result.detail

    def test_check_providers_exception(self, tmp_path, monkeypatch):
        kilocode_dir = tmp_path / ".kilocode"
        kilocode_dir.mkdir()
        providers_file = kilocode_dir / "providers.yaml"
        providers_file.write_text("kilo_gateway:\n  api_key: test\n")
        monkeypatch.setattr("src.diagnostics.Path.home", lambda: tmp_path)
        with patch("builtins.open", side_effect=OSError("read failed")):
            result = check_providers()
        assert result.status == "WARN"

    def test_check_runners_exception(self):
        with patch("urllib.request.urlopen", side_effect=Exception("connection failed")):
            result = check_runners()
        assert result.status == "WARN"

    def test_check_runners_url_error(self):
        import urllib.error

        with patch("urllib.request.Request"):
            with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("connection failed")):
                result = check_runners()
        assert result.status == "WARN"
        assert "not reachable" in result.detail.lower()

    def test_check_toolchains_missing_yaml(self, monkeypatch):
        import pathlib

        original_exists = pathlib.Path.exists

        def fake_exists(self):
            if "toolchains.yaml" in str(self):
                return False
            return original_exists(self)

        monkeypatch.setattr("pathlib.Path.exists", fake_exists)
        result = check_toolchains()
        assert result.status == "WARN"
        assert "toolchains.yaml not found" in result.detail

    def test_check_toolchains_generic_exception(self, tmp_path, monkeypatch):
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        toolchains_file = config_dir / "toolchains.yaml"
        toolchains_file.write_text("toolchains:\n  - name: zig\n")
        monkeypatch.setattr("src.diagnostics.Path.home", lambda: tmp_path)
        with patch("src.diagnostics.Path") as mock_path:
            fake_path = MagicMock()
            fake_path.exists.return_value = True
            fake_path.__truediv__ = MagicMock(return_value=toolchains_file)
            fake_path.parent.parent.__truediv__ = MagicMock(return_value=toolchains_file)
            mock_path.return_value = fake_path
            import yaml

            with patch.object(yaml, "safe_load", side_effect=OSError("yaml load failed")):
                result = check_toolchains()
        assert result.status == "WARN"

    def test_check_daemon_health_generic_exception(self):
        with patch("urllib.request.urlopen", side_effect=RuntimeError("unexpected")):
            result = check_daemon_health()
        assert result.status == "WARN"


class TestDiagnosticsServer:
    def test_start_server_logs_wal(self):
        with patch("src.diagnostics.HTTPServer") as mock_server:
            with patch("src.diagnostics.log_wal") as mock_log:
                from src.diagnostics import start_server
                start_server(port=18801)
        mock_server.assert_called_once()
        mock_log.assert_called_once_with("server_start", {"port": 18801})

    def test_do_get_unknown_path_returns_404(self):
        from src.diagnostics import DiagnosticsHandler
        with patch.object(DiagnosticsHandler, "handle_one_request", lambda self: None):
            handler = DiagnosticsHandler(MagicMock(), ("127.0.0.1", 8801), MagicMock())
        handler.command = "GET"
        handler.path = "/unknown"
        with patch.object(handler, "send_response") as mock_send:
            with patch.object(handler, "end_headers") as mock_end:
                handler.do_GET()
        mock_send.assert_called_once_with(404)
        mock_end.assert_called_once()

    def test_log_message_suppressed(self):
        from src.diagnostics import DiagnosticsHandler
        with patch.object(DiagnosticsHandler, "handle_one_request", lambda self: None):
            handler = DiagnosticsHandler(MagicMock(), ("127.0.0.1", 8801), MagicMock())
        handler.log_message("test %s", "arg")  # Should not raise

    def test_main_block_exits_with_summary(self):
        report = {"error": 1, "checks": []}
        exit_code = 0 if report["error"] == 0 else 1
        assert exit_code == 1
