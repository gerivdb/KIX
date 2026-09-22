"""Shared pytest fixtures for KIX tests."""

import sys
from pathlib import Path

import pytest
from src.app import app as kix_app

# Ajouter libs/ au path pour les imports shared-clients
_LIBS_DIR = Path(__file__).resolve().parent.parent / "libs"
if str(_LIBS_DIR) not in sys.path:
    sys.path.insert(0, str(_LIBS_DIR))


@pytest.fixture
def client():
    kix_app.config["TESTING"] = True
    with kix_app.test_client() as client:
        yield client
