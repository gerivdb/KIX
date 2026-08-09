"""
KIX Diagnostics Module — Agent Manager Diagnostics
IntentHash: 0xPRD_MOC_AGENT_MANAGER_DIAGNOSTICS_20260809
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Any

# WAL NEXUS integration
WAL_DIR = Path(__file__).resolve().parent.parent / ".kilo" / "wal"
WAL_FILE = WAL_DIR / "kix-diagnostics.jsonl"


def log_wal(event_type: str, data: dict[str, Any]) -> None:
    """Logger un événement dans WAL NEXUS."""
    WAL_DIR.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event_type": event_type,
        "intent_hash": "0xPRD_MOC_AGENT_MANAGER_DIAGNOSTICS_20260809",
        "data": data,
    }
    with open(WAL_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


class DiagnosticsResult:
    """Conteneur pour résultats de diagnostic."""

    def __init__(self, check: str):
        self.check = check
        self.status = "OK"
        self.detail = ""
        self.timestamp = datetime.utcnow().isoformat() + "Z"

    def set_error(self, detail: str) -> None:
        self.status = "ERROR"
        self.detail = detail

    def set_warn(self, detail: str) -> None:
        self.status = "WARN"
        self.detail = detail

    def to_dict(self) -> dict[str, Any]:
        return {
            "check": self.check,
            "status": self.status,
            "detail": self.detail,
            "timestamp": self.timestamp,
        }


def check_kilocode_cli() -> DiagnosticsResult:
    """Vérifier que kilocode CLI est disponible."""
    result = DiagnosticsResult("kilocode_cli")
    try:
        subprocess.run(
            ["kilocode", "--version"],
            capture_output=True,
            check=True,
            timeout=10,
        )
        result.detail = "kilocode CLI available"
    except FileNotFoundError:
        result.set_error("kilocode not found in PATH")
    except subprocess.TimeoutExpired:
        result.set_error("kilocode CLI timeout")
    except Exception as e:
        result.set_error(f"kilocode check failed: {e}")
    return result


def check_auth() -> DiagnosticsResult:
    """Vérifier que l'authentification kilocode est valide."""
    result = DiagnosticsResult("kilocode_auth")
    try:
        proc = subprocess.run(
            ["kilocode", "auth", "login"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if proc.returncode == 0 or "already logged in" in proc.stdout.lower():
            result.detail = "Token valid"
        else:
            result.set_error(f"Auth failed: {proc.stderr or proc.stdout}")
    except Exception as e:
        result.set_error(f"Auth check failed: {e}")
    return result


def check_providers() -> DiagnosticsResult:
    """Vérifier que les providers sont configurés."""
    result = DiagnosticsResult("providers")
    providers_file = Path.home() / ".kilocode" / "providers.yaml"
    if not providers_file.exists():
        result.set_warn("providers.yaml not found")
        return result

    try:
        with open(providers_file, "r", encoding="utf-8") as f:
            content = f.read()
        providers = []
        for name in ["kilo_gateway", "openai", "anthropic", "google"]:
            if name in content:
                providers.append(name)
        if providers:
            result.detail = f"Configured: {', '.join(providers)}"
        else:
            result.set_warn("No providers configured")
    except Exception as e:
        result.set_warn(f"Cannot read providers: {e}")
    return result


def check_runners() -> DiagnosticsResult:
    """Vérifier les statuts des runners RLM/TLM/LLM via KIX."""
    result = DiagnosticsResult("kix_runners")
    try:
        # KIX tourne sur port 8800
        import urllib.request
        req = urllib.request.Request(
            "http://localhost:8800/health",
            timeout=5,
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            runners = data.get("runners", {})
            result.detail = f"Runners: {', '.join(runners.keys())}"
    except urllib.error.URLError:
        result.set_warn("KIX not reachable on port 8800")
    except Exception as e:
        result.set_warn(f"Runner check failed: {e}")
    return result


def run_all_checks() -> dict[str, Any]:
    """Exécuter tous les checks et retourner le rapport."""
    checks = [
        check_kilocode_cli,
        check_auth,
        check_providers,
        check_runners,
    ]
    results = []
    for check_fn in checks:
        res = check_fn()
        results.append(res.to_dict())
        log_wal("diagnostic_check", res.to_dict())

    summary = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "total": len(results),
        "ok": sum(1 for r in results if r["status"] == "OK"),
        "warn": sum(1 for r in results if r["status"] == "WARN"),
        "error": sum(1 for r in results if r["status"] == "ERROR"),
        "checks": results,
    }
    log_wal("diagnostic_summary", summary)
    return summary


class DiagnosticsHandler(BaseHTTPRequestHandler):
    """HTTP handler pour endpoint /agent-manager/diagnostics."""

    def do_GET(self) -> None:
        if self.path == "/agent-manager/diagnostics":
            report = run_all_checks()
            status = 200 if report["error"] == 0 else 500
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(report, ensure_ascii=False).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format: str, *args: Any) -> None:
        pass  # Suppress default logging


def start_server(port: int = 8801) -> None:
    """Démarrer le serveur de diagnostics KIX."""
    server = HTTPServer(("localhost", port), DiagnosticsHandler)
    log_wal("server_start", {"port": port})
    print(f"KIX Diagnostics server running on port {port}")
    print(f"Endpoint: http://localhost:{port}/agent-manager/diagnostics")
    server.serve_forever()


if __name__ == "__main__":
    if "--server" in sys.argv:
        port = int(sys.argv[sys.argv.index("--server") + 1]) if "--server" in sys.argv and len(sys.argv) > sys.argv.index("--server") + 1 else 8801
        start_server(port)
    else:
        report = run_all_checks()
        print(json.dumps(report, ensure_ascii=False, indent=2))
        sys.exit(0 if report["error"] == 0 else 1)
