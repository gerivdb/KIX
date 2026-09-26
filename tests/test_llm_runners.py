#!/usr/bin/env python3
"""Tests basiques pour endpoints LLM KIX."""
from __future__ import annotations

import pytest


@pytest.mark.skip(reason="KIX must be started manually on port 8800")
def test_kix_health():
    import requests

    r = requests.get("http://127.0.0.1:8800/health", timeout=2)
    assert r.status_code == 200


@pytest.mark.skip(reason="KIX must be started manually on port 8800")
def test_kix_llm_runners():
    import requests

    r = requests.get("http://127.0.0.1:8800/runners/llm", timeout=2)
    assert r.status_code == 200
    data = r.json()
    assert "runners" in data
    ports = {x["port"] for x in data["runners"]}
    assert 18000 in ports
    assert 9000 in ports


@pytest.mark.skip(reason="KIX must be started manually on port 8800")
def test_kix_llm_status():
    import requests

    r = requests.get("http://127.0.0.1:8800/runners/18000/status", timeout=2)
    assert r.status_code == 200
    data = r.json()
    assert data["service"] == "llm-gateway"


@pytest.mark.skip(reason="KIX must be started manually on port 8800")
def test_kix_llm_start_stop():
    import requests

    r = requests.post("http://127.0.0.1:8800/runners/18000/start", timeout=5)
    assert r.status_code == 200
    r = requests.post("http://127.0.0.1:8800/runners/18000/stop", timeout=5)
    assert r.status_code == 200
