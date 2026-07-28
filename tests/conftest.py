"""Shared pytest fixtures for KIX tests."""

import pytest
from src.app import app as kix_app


@pytest.fixture
def client():
    kix_app.config["TESTING"] = True
    with kix_app.test_client() as client:
        yield client
