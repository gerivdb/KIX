"""Wrapper runner pour binaires Zig (TRIX, LLUX, TIMX, ROOTX, TLM-LANG)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from runners.base import RunnerBase, RunnerSpec


class ZigBinaryRunner(RunnerBase):
    def start(self) -> dict:
        binary = self.spec.binary
        if not binary:
            return {"status": "error", "detail": "binary requis pour runner zig-binary"}

        binary_path = Path(self.spec.working_dir) / binary
        if not binary_path.exists():
            return {"status": "error", "detail": f"binaire introuvable: {binary_path}"}

        if self.spec.build and self.spec.build.get("pre_start"):
            build_cmd = self.spec.build.get("command", ["zig", "build"])
            try:
                result = subprocess.run(
                    build_cmd,
                    cwd=str(self.spec.working_dir),
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                if result.returncode != 0:
                    return {"status": "error", "detail": f"build echoue: {result.stderr}"}
            except Exception as exc:
                return {"status": "error", "detail": f"build erreur: {exc}"}

        cmd = [str(binary_path)]
        if self.spec.command:
            cmd.extend(self.spec.command)

        log_file = self._resolve_log_file()
        log_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(log_file, "a", encoding="utf-8") as log:
                log.write(f"[KIX] launching {' '.join(cmd)} at ...\n")
            if sys.platform == "win32":
                proc = subprocess.Popen(
                    cmd,
                    cwd=str(self.spec.working_dir),
                    creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
                )
            else:
                proc = subprocess.Popen(cmd, cwd=str(self.spec.working_dir), start_new_session=True)
            return {"status": "starting", "pid": proc.pid}
        except (OSError, ValueError) as exc:
            return {"status": "error", "detail": str(exc)}

    def stop(self, pid: int) -> dict:
        try:
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/F", "/PID", str(pid)], check=False)
            else:
                os.kill(pid, 9)
        except OSError:
            pass
        return {"status": "stopped", "pid": pid}

    def status(self, pid: int) -> dict:
        alive = _is_process_alive(pid)
        return {"status": "running" if alive else "stopped", "pid": pid}

    def health(self) -> dict:
        return _probe_http(self.spec.port, self.spec.health_path, self.spec.health_timeout)

    def logs(self, lines: int = 100) -> str:
        log_file = self._resolve_log_file()
        if not log_file.exists():
            return ""
        try:
            with open(log_file, "r", encoding="utf-8") as fh:
                return "".join(fh.readlines()[-lines:])
        except Exception:
            return ""

    def restart(self, pid: int) -> dict:
        self.stop(pid)
        return self.start()

    def _resolve_log_file(self) -> Path:
        if self.spec.log_file:
            return self.spec.log_file
        return Path(self.spec.working_dir) / "data" / f"{self.spec.name}.log"


def _is_process_alive(pid: int) -> bool:
    if sys.platform == "win32":
        cmd = f"Get-Process -Id {pid} -ErrorAction SilentlyContinue"
        return os.system(f"powershell -Command \"{cmd}\"") == 0
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, OSError):
        return False


def _probe_http(port: int, path: str, timeout: float) -> dict:
    import requests

    url = f"http://localhost:{port}{path}"
    try:
        resp = requests.get(url, timeout=timeout)
        if resp.status_code == 200:
            return {"status": "ok", "http_status": resp.status_code}
        return {"status": "unhealthy", "http_status": resp.status_code}
    except Exception as exc:
        return {"status": "unreachable", "detail": str(exc)}
