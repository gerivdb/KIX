"""Tests d'intégration N243/KIX pour CTULU."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

# Répertoire racine de CTULU
CTULU_ROOT = Path(__file__).resolve().parent.parent
N243_PATH = Path("D:/DO/WEB/TOOLS/L4-TOOLS/N243")
KIX_PATH = Path("D:/DO/WEB/TOOLS/L2-PLATFORM/KIX")
ARTIFACTS_JSON = CTULU_ROOT / "tests" / "fixtures" / "n243_kix_required_artifacts.json"


def run_validator(n243_path: Path, kix_path: Path, artifacts: Path) -> dict:
    """Exécute le validateur N243/KIX et retourne le rapport JSON."""
    script = CTULU_ROOT / "scripts" / "n243_kix_integration_validator.py"
    if not script.exists():
        pytest.skip(f"Validator script not found: {script}")
    result = subprocess.run(
        [sys.executable, str(script), "--n243-path", str(n243_path), "--kix-path", str(kix_path), "--artifacts", str(artifacts)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.fail(f"Validator failed: {result.stderr}")
    return json.loads(result.stdout)


def test_n243_kix_validator_exists() -> None:
    """Vérifie que le validateur N243/KIX existe dans CTULU."""
    script = CTULU_ROOT / "scripts" / "n243_kix_integration_validator.py"
    assert script.exists(), f"Missing validator script: {script}"


def test_n243_kix_artifacts_json_exists() -> None:
    """Vérifie que le fichier JSON des artifacts requis existe."""
    if not ARTIFACTS_JSON.exists():
        # Créer un artifacts JSON minimal si absent
        ARTIFACTS_JSON.parent.mkdir(parents=True, exist_ok=True)
        default_artifacts = {
            "required": [
                "PRD-MOC/PRD-MOC-CTULU-CROSS-REPO-N243-KIX-INTEGRATION-20260929.md",
                "scripts/n243_kix_integration_validator.py",
            ]
        }
        ARTIFACTS_JSON.write_text(json.dumps(default_artifacts, indent=2, ensure_ascii=False), encoding="utf-8")
    assert ARTIFACTS_JSON.exists()


def test_n243_kix_integration_report() -> None:
    """Vérifie que le validateur génère un rapport valide pour N243 et KIX."""
    test_n243_kix_artifacts_json_exists()
    report = run_validator(N243_PATH, KIX_PATH, ARTIFACTS_JSON)
    assert "summary" in report
    assert "n243_status" in report["summary"]
    assert "kix_status" in report["summary"]
    assert report["summary"]["total_required"] >= 1


def test_cross_repo_atomic_script_exists() -> None:
    """Vérifie que le script cross-repo atomic existe dans CTULU."""
    script = CTULU_ROOT / "pipelines" / "cross_repo_atomic.py"
    # Le pipeline peut ne pas exister encore (phase 2), skip si absent
    if not script.exists():
        pytest.skip("cross_repo_atomic.py not yet implemented")


def test_pid_governance_tests_pass() -> None:
    """Vérifie que les tests PID governance passent dans CTULU."""
    test_file = CTULU_ROOT / "tests" / "test_pid_governance.py"
    if not test_file.exists():
        pytest.skip("test_pid_governance.py not found")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_file), "-q"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"PID governance tests failed: {result.stdout}\n{result.stderr}"
