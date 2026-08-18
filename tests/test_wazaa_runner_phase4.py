"""Tests d'intégration spécifiques WAZAA (Phase 4).

Valide le wrapper PythonRunner pour WAZAA avec :
- Entrypoint tools/mission_control/server.py
- Health-check /healthz sur port 5002
- Dépendance kix (depends_on)
- Restart policy on-failure
- WAZAA ne dépend PAS de BUZZ-X
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from runners.base import RunnerSpec
from runners.python_runner import PythonRunner


@pytest.fixture()
def wazaa_spec(tmp_path: Path) -> RunnerSpec:
    return RunnerSpec(
        name="wazaa",
        runner_type="python",
        port=5002,
        working_dir=tmp_path,
        entrypoint="tools/mission_control/server.py",
        health_path="/healthz",
        health_timeout=5.0,
        depends_on=["kix"],
        restart_policy="on-failure",
        log_file=tmp_path / "data" / "wazaa.log",
        meta={"repo": "gerivdb/WAZAA", "role": "multi-agent orchestration"},
    )


class TestWazaaRunnerPhase4:
    def test_start_launches_entrypoint(self, wazaa_spec: RunnerSpec) -> None:
        (wazaa_spec.working_dir / "tools" / "mission_control").mkdir(parents=True)
        (wazaa_spec.working_dir / "tools" / "mission_control" / "server.py").write_text(
            "print('ok')", encoding="utf-8"
        )
        runner = PythonRunner(wazaa_spec)
        with patch("subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.pid = 5002
            mock_popen.return_value = mock_proc
            result = runner.start()
        assert result["status"] == "starting"
        assert result["pid"] == 5002
        args, kwargs = mock_popen.call_args
        assert args[0][-1].endswith("server.py")
        assert kwargs["cwd"] == str(wazaa_spec.working_dir)

    def test_does_not_depend_on_buzz(self, wazaa_spec: RunnerSpec) -> None:
        # WAZAA ne doit pas avoir BUZZ-X dans depends_on
        assert "buzz" not in wazaa_spec.depends_on
        assert wazaa_spec.depends_on == ["kix"]

    def test_health_ok(self, wazaa_spec: RunnerSpec) -> None:
        runner = PythonRunner(wazaa_spec)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        with patch("requests.get", return_value=mock_resp):
            result = runner.health()
        assert result["status"] == "ok"

    def test_logs(self, wazaa_spec: RunnerSpec) -> None:
        log_path = wazaa_spec.working_dir / "data" / "wazaa.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text("wazaa-start\nwazaa-ready\n", encoding="utf-8")
        runner = PythonRunner(wazaa_spec)
        assert runner.logs(lines=1) == "wazaa-ready\n"
