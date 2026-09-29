"""Shared pytest fixtures for KIX tests."""

import sys
from pathlib import Path

import pytest

# Ajouter src/ au path pour les imports KIX
_SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

# Ajouter libs/ au path pour les imports shared-clients
_LIBS_DIR = Path(__file__).resolve().parent.parent / "libs"
if str(_LIBS_DIR) not in sys.path:
    sys.path.insert(0, str(_LIBS_DIR))

# Ajouter services/ au path pour les runners KIX
_SERVICES_DIR = Path(__file__).resolve().parent.parent / "services"
if str(_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(_SERVICES_DIR))

from src.app import app as kix_app


@pytest.fixture
def client():
    kix_app.config["TESTING"] = True
    with kix_app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def _isolate_cognitive_runner():
    for mod_name in list(sys.modules):
        if mod_name == "conversation_cognitive_runner" or mod_name.startswith("conversation_cognitive_runner."):
            del sys.modules[mod_name]
    yield
    for mod_name in list(sys.modules):
        if mod_name == "conversation_cognitive_runner" or mod_name.startswith("conversation_cognitive_runner."):
            del sys.modules[mod_name]
