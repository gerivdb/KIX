"""Tests for src/app.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from src.app import Runner, _utcnow, _load_known_repositories, _is_process_alive, _probe_port, app as flask_app


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    return flask_app.test_client()


class TestRunner:
    def test_create_runner(self):
        runner = Runner(name="trixd", port=8742)
        assert runner.name == "trixd"
        assert runner.port == 8742
        assert runner.status == "unknown"

    def test_to_dict(self):
        runner = Runner(name="trixd", port=8742, status="running", pid=1234)
        data = runner.to_dict()
        assert data["name"] == "trixd"
        assert data["port"] == 8742
        assert data["status"] == "running"
        assert data["pid"] == 1234


class TestUtcnow:
    def test_utcnow_returns_iso_string(self):
        result = _utcnow()
        assert isinstance(result, str)
        assert len(result) > 0
        assert "T" in result


class TestLoadKnownRepositories:
    def test_missing_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "src.app.KNOWN_REPO_FILE",
            tmp_path / "missing.yaml",
        )
        result = _load_known_repositories()
        assert result == []

    def test_valid_yaml(self, tmp_path, monkeypatch):
        yaml_file = tmp_path / "known_repositories.yaml"
        yaml_file.write_text("""
repos:
  - repo: test-repo
    port: 8742
  - "string-entry"
""")
        monkeypatch.setattr(
            "src.app.KNOWN_REPO_FILE",
            yaml_file,
        )
        result = _load_known_repositories()
        assert len(result) == 1
        assert result[0].name == "test-repo"
        assert result[0].port == 8742


class TestIsProcessAlive:
    def test_is_alive_windows(self, monkeypatch):
        monkeypatch.setattr("sys.platform", "win32")
        with patch("src.app.os.system", return_value=0):
            assert _is_process_alive(1234) is True
        with patch("src.app.os.system", return_value=1):
            assert _is_process_alive(1234) is False

    def test_is_alive_linux(self, monkeypatch):
        monkeypatch.setattr("sys.platform", "linux")
        with patch("src.app.os.kill", side_effect=None):
            assert _is_process_alive(1234) is True
        with patch("src.app.os.kill", side_effect=ProcessLookupError()):
            assert _is_process_alive(1234) is False


class TestProbePort:
    def test_probe_port_open(self):
        with patch("socket.socket") as mock_socket:
            mock_sock = MagicMock()
            mock_socket.return_value.__enter__.return_value = mock_sock
            assert _probe_port(8742) is True

    def test_probe_port_closed(self):
        with patch("socket.socket") as mock_socket:
            mock_sock = MagicMock()
            mock_sock.connect.side_effect = OSError()
            mock_socket.return_value.__enter__.return_value = mock_sock
            assert _probe_port(8742) is False


class TestAppRoutes:
    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"
        assert data["service"] == "kix"

    def test_healthz(self, client):
        resp = client.get("/healthz")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"

    def test_health_kix_alias(self, client):
        resp = client.get("/health/kix")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["service"] == "kix"

    def test_readyz_ok(self, client, tmp_path, monkeypatch):
        db = tmp_path / "kix.sqlite"
        db.write_text("")
        monkeypatch.setenv("KIX_DB", str(db))
        monkeypatch.setenv("KIX_NOTIFICATIONS_DB", str(tmp_path / "notifications.db"))
        monkeypatch.setenv("KIX_AUDIT_DB", str(tmp_path / "audit.db"))
        (tmp_path / "notifications.db").write_text("")
        (tmp_path / "audit.db").write_text("")
        resp = client.get("/readyz")
        assert resp.status_code in (200, 503)

    def test_vote(self, client):
        resp = client.get("/vote")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "vote" in data
        assert "by_status" in data

    def test_login_missing_credentials(self, client):
        resp = client.post("/login", json={})
        assert resp.status_code == 400

    def test_login_invalid_credentials(self, client, monkeypatch):
        monkeypatch.setattr(
            "src.app._load_users",
            lambda: {"admin": {"password": "secret", "role": "admin"}},
        )
        resp = client.post("/login", json={"username": "admin", "password": "wrong"})
        assert resp.status_code == 401

    def test_login_success(self, client, monkeypatch):
        monkeypatch.setattr(
            "src.app._load_users",
            lambda: {"admin": {"password": "secret", "role": "admin"}},
        )
        resp = client.post("/login", json={"username": "admin", "password": "secret"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert "access_token" in data

    def test_metrics(self, client, monkeypatch):
        monkeypatch.setattr(
            "src.app._load_users",
            lambda: {"admin": {"password": "secret", "role": "admin"}},
        )
        login = client.post("/login", json={"username": "admin", "password": "secret"}).get_json()
        headers = {"Authorization": f"Bearer {login['access_token']}"}
        resp = client.get("/metrics", headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["service"] == "kix"

    def test_runners_empty(self, client, monkeypatch):
        monkeypatch.setattr(
            "src.app._load_users",
            lambda: {"admin": {"password": "secret", "role": "admin"}},
        )
        login = client.post("/login", json={"username": "admin", "password": "secret"}).get_json()
        headers = {"Authorization": f"Bearer {login['access_token']}"}
        monkeypatch.setattr(
            "src.app._load_known_repositories",
            lambda: [],
        )
        monkeypatch.setattr(
            "src.app._load_runners_config",
            lambda: [],
        )
        resp = client.get("/runners", headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "runners" in data

    def test_runner_status_not_found(self, client, monkeypatch):
        monkeypatch.setattr(
            "src.app._load_users",
            lambda: {"admin": {"password": "secret", "role": "admin"}},
        )
        login = client.post("/login", json={"username": "admin", "password": "secret"}).get_json()
        headers = {"Authorization": f"Bearer {login['access_token']}"}
        monkeypatch.setattr(
            "src.app._load_known_repositories",
            lambda: [],
        )
        monkeypatch.setattr(
            "src.app._load_runners_config",
            lambda: [],
        )
        resp = client.get("/runners/unknown/status", headers=headers)
        assert resp.status_code == 404

    def test_register_runner(self, client, monkeypatch):
        monkeypatch.setattr(
            "src.app._load_users",
            lambda: {"admin": {"password": "secret", "role": "admin"}},
        )
        login = client.post("/login", json={"username": "admin", "password": "secret"}).get_json()
        headers = {"Authorization": f"Bearer {login['access_token']}"}
        resp = client.post("/runners/register", json={"name": "new-runner", "port": 8742}, headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "registered"

    def test_schedule_cycle(self, client, monkeypatch):
        monkeypatch.setattr(
            "src.app._load_users",
            lambda: {"admin": {"password": "secret", "role": "admin"}},
        )
        login = client.post("/login", json={"username": "admin", "password": "secret"}).get_json()
        headers = {"Authorization": f"Bearer {login['access_token']}"}
        resp = client.post("/schedule/cycle", json={"service": "PLIX", "cron": "0 0 * * *", "action": "backup"}, headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "scheduled"

    def test_list_schedules(self, client, monkeypatch):
        monkeypatch.setattr(
            "src.app._load_users",
            lambda: {"admin": {"password": "secret", "role": "admin"}},
        )
        login = client.post("/login", json={"username": "admin", "password": "secret"}).get_json()
        headers = {"Authorization": f"Bearer {login['access_token']}"}
        resp = client.get("/schedules", headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "total" in data

    def test_stop_runner_not_found(self, client, monkeypatch):
        monkeypatch.setattr(
            "src.app._load_users",
            lambda: {"admin": {"password": "secret", "role": "admin"}},
        )
        login = client.post("/login", json={"username": "admin", "password": "secret"}).get_json()
        headers = {"Authorization": f"Bearer {login['access_token']}"}
        monkeypatch.setattr(
            "src.app._load_known_repositories",
            lambda: [],
        )
        monkeypatch.setattr(
            "src.app._load_runners_config",
            lambda: [],
        )
        resp = client.post("/runners/unknown/stop", headers=headers)
        assert resp.status_code == 404

    def test_runner_health_not_found(self, client, monkeypatch):
        monkeypatch.setattr(
            "src.app._load_users",
            lambda: {"admin": {"password": "secret", "role": "admin"}},
        )
        login = client.post("/login", json={"username": "admin", "password": "secret"}).get_json()
        headers = {"Authorization": f"Bearer {login['access_token']}"}
        monkeypatch.setattr(
            "src.app._get_runner_instance",
            lambda name: None,
        )
        resp = client.get("/runners/unknown/health", headers=headers)
        assert resp.status_code == 404

    def test_list_zombies(self, client, monkeypatch):
        monkeypatch.setattr(
            "src.app._load_users",
            lambda: {"admin": {"password": "secret", "role": "admin"}},
        )
        login = client.post("/login", json={"username": "admin", "password": "secret"}).get_json()
        headers = {"Authorization": f"Bearer {login['access_token']}"}
        monkeypatch.setattr(
            "src.zombie_monitor.get_process_zombies",
            lambda: [],
        )
        monkeypatch.setattr(
            "src.zombie_monitor.get_worktree_zombies",
            lambda: [],
        )
        monkeypatch.setattr(
            "src.zombie_monitor.get_stash_zombies",
            lambda: [],
        )
        resp = client.get("/health/zombies", headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["service"] == "kix"

    def test_list_conflicts(self, client, monkeypatch):
        monkeypatch.setattr(
            "src.app._load_users",
            lambda: {"admin": {"password": "secret", "role": "admin"}},
        )
        login = client.post("/login", json={"username": "admin", "password": "secret"}).get_json()
        headers = {"Authorization": f"Bearer {login['access_token']}"}
        monkeypatch.setattr(
            "src.zombie_monitor.detect_conflicts",
            lambda: [],
        )
        resp = client.get("/health/conflicts", headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["service"] == "kix"

    def test_purge_zombies_endpoint(self, client, monkeypatch):
        monkeypatch.setattr(
            "src.app._load_users",
            lambda: {"admin": {"password": "secret", "role": "admin"}},
        )
        login = client.post("/login", json={"username": "admin", "password": "secret"}).get_json()
        headers = {"Authorization": f"Bearer {login['access_token']}"}
        monkeypatch.setattr(
            "src.zombie_monitor.purge_zombies",
            lambda types=None, repo=None, worktree=None, priority="high", dry_run=True: {
                "status": "dry_run",
                "purged": [],
                "errors": [],
                "wal_logged": True,
            },
        )
        resp = client.post("/health/zombies/purge", json={"dry_run": True}, headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "dry_run"
