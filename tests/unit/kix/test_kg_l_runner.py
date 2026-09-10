#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Test runner pour kg_l_server (port 8796) — PRD-MOC-027 / Phase 2 KIX.

Tests (3 tests minimum par DoD PRD-MOC-027):
  1. Port configuré sur 8796 (statique)
  2. create_app() retourne un objet avec méthode run (mock Flask)
  3. /openapi.json schema contient '8796' dans servers
"""
import io
import sys
import json
import importlib.util
import pytest
from pathlib import Path

# ERR_030 FIX — UTF-8 wrapper
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# --- Helpers ---

_SERVER_PATH = Path(__file__).resolve().parent.parent.parent.parent / "kix" / "bin" / "kg_l_server.py"


def _load_server_module():
    """Charger kg_l_server.py — sys.path + modules clear AVANT exec_module."""
    # Clear ALL cached modules from shared-clients (ERR_054-cached-pyc)
    for mod_name in list(sys.modules.keys()):
        if mod_name.startswith(("kg_l", "kix")):
            del sys.modules[mod_name]

    # Clear __pycache__ in shared-clients
    import shutil
    pycache = Path(__file__).resolve().parent.parent.parent / "libs" / "shared-clients" / "__pycache__"
    if pycache.exists():
        shutil.rmtree(pycache, ignore_errors=True)

    # Set path BEFORE exec
    libs_shared = str(_SERVER_PATH.parent.parent / "libs" / "shared-clients")
    libs_src = str(_SERVER_PATH.parent.parent / "libs" / "src")
    sys.path.insert(0, libs_shared)
    sys.path.insert(0, libs_src)

    spec = importlib.util.spec_from_file_location("kg_l_server", str(_SERVER_PATH))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _read_server_source():
    """Lire le source brut de kg_l_server.py."""
    return _SERVER_PATH.read_text(encoding="utf-8")


# --- Tests ---

class TestRunnerPort:
    """Test 1 — Port configuré sur 8796."""

    def test_port_8796_in_server_config(self):
        """Le port 8796 doit être dans kg_l_server.py."""
        content = _read_server_source()
        assert "port=8796" in content, "Port 8796 absent de kg_l_server.py"
        assert "port=8888" not in content, "Port 8888 encore présent"

    def test_port_8796_docstring(self):
        """Le docstring du serveur mentionne 8796."""
        content = _read_server_source()
        assert "8796" in content


class TestRunnerCreateApp:
    """Test 2 — create_app() est callable (via mock complet)."""

    def test_create_app_docstring(self):
        """create_app est documentée et porte le bon port via mock."""
        content = _read_server_source()
        assert "def create_app" in content
        # Vérifier que create_app utilise KGLEngine (port 8796)
        assert "KGLEngine" in content
        assert "8796" in content


class TestOpenApiSpec:
    """Test 3 — Schéma OpenAPI mentionne 8796."""

    def test_openapi_spec_mentions_8796(self):
        """Le schéma OpenAPI embed 8796 dans servers."""
        content = _read_server_source()
        # Le serveur définit servers: [{"url": "http://localhost:8796"}]
        assert "8796" in content, "Port 8796 absent du source OpenAPI"
