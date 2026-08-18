"""Tests d'intégration spécifiques TRIX (Phase 3).

Valide le wrapper ZigBinaryRunner avec :
- Build automatique zig build trixd avant start
- Health-check /healthz sur port 7243
- Restart policy on-failure
- Logs fichier trixd.log
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from runners.base import RunnerSpec
from runners.zig_runner import ZigBinaryRunner


@pytest.fixture()
def trix_spec(tmp_path: Path) -> RunnerSpec:
    return RunnerSpec(
        name="trixd",
        runner_type="zig-binary",
        port=7243,
        working_dir=tmp_path,
        binary="zig-out/bin/trixd.exe",
        build={
            "command": ["zig", "build", "trixd"],
            "required": True,
            "pre_start": True,
        },
        health_path="/healthz",
        health_timeout=5.0,
        depends_on=["kix"],
        restart_policy="on-failure",
        log_file=tmp_path / "data" / "trixd.log",
        meta={"repo": "gerivdb/TRIX", "role": "zig runtime"},
    )


class TestZigBinaryRunnerPhase3:
    def test_start_build_pre_start_success(self, trix_spec: RunnerSpec) -> None:
        (trix_spec.working_dir / "zig-out" / "bin").mkdir(parents=True)
        (trix_spec.working_dir / "zig-out" / "bin" / "trixd.exe").write_text("", encoding="utf-8")
        runner = ZigBinaryRunner(trix_spec)
        with patch("subprocess.run") as mock_run, patch("subprocess.Popen") as mock_popen:
            mock_run.return_value.returncode = 0
            mock_proc = MagicMock()
            mock_proc.pid = 7243
            mock_popen.return_value = mock_proc
            result = runner.start()
        assert result["status"] == "starting"
        assert result["pid"] == 7243
        assert mock_run.called
        build_call = mock_run.call_args_list[0]
        assert build_call[0][0] == ["zig", "build", "trixd"]

    def test_start_build_pre_start_failure(self, trix_spec: RunnerSpec) -> None:
        runner = ZigBinaryRunner(trix_spec)
        with patch("subprocess.run", side_effect=Exception("build boom")):
            result = runner.start()
        assert result["status"] == "error"
        assert "build" in result["detail"].lower() or "erreur" in result["detail"].lower()

    def test_start_missing_binary(self, trix_spec: RunnerSpec) -> None:
        runner = ZigBinaryRunner(trix_spec)
        result = runner.start()
        assert result["status"] == "error"
        assert "introuvable" in result["detail"]

    def test_start_no_build_when_not_pre_start(self, tmp_path: Path) -> None:
        spec = RunnerSpec(
            name="trixd-fast",
            runner_type="zig-binary",
            port=7243,
            working_dir=tmp_path,
            binary="trixd.exe",
            build={"command": ["zig", "build", "trixd"], "required": True, "pre_start": False},
            health_path="/health",
        )
        (tmp_path / "trixd.exe").write_text("", encoding="utf-8")
        runner = ZigBinaryRunner(spec)
        with patch("subprocess.run") as mock_run, patch("subprocess.Popen") as mock_popen:
            mock_popen.return_value = MagicMock(pid=7244)
            runner.start()
        assert not mock_run.called

    def test_health_ok(self, trix_spec: RunnerSpec) -> None:
        runner = ZigBinaryRunner(trix_spec)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        with patch("requests.get", return_value=mock_resp):
            result = runner.health()
        assert result["status"] == "ok"

    def test_health_unreachable(self, trix_spec: RunnerSpec) -> None:
        runner = ZigBinaryRunner(trix_spec)
        with patch("requests.get", side_effect=Exception("conn refused")):
            result = runner.health()
        assert result["status"] == "unreachable"

    def test_logs(self, trix_spec: RunnerSpec) -> None:
        log_path = trix_spec.working_dir / "data" / "trixd.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text("a\nb\nc\n", encoding="utf-8")
        runner = ZigBinaryRunner(trix_spec)
        assert runner.logs(lines=2) == "b\nc\n"
