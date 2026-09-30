"""Minimal REST client for TRIX Git Arbiter (port 8742)."""

import json
import urllib.request
import urllib.error


BASE_URL = "http://127.0.0.1:8742"


def _request(url: str, data: dict | None = None) -> dict:
    """Send an HTTP request and return JSON response or error dict."""
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8") if data is not None else None,
            headers={"Content-Type": "application/json"},
            method="POST" if data is not None else "GET",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (ConnectionResetError, ConnectionAbortedError, urllib.error.URLError, json.JSONDecodeError) as exc:
        return {"error": str(exc)}


def release_lock(branch: str, agent_id: str) -> dict:
    """Release a worktree lock on a branch.

    Args:
        branch: The branch name.
        agent_id: The agent identifier.

    Returns:
        JSON response from the server or {"error": "..."}.
    """
    return _request(f"{BASE_URL}/git/locks/release", {"branch": branch, "agent_id": agent_id})


def get_worktree_locks() -> dict:
    """Return all active worktree locks.

    Returns:
        Dict with "locks" key or {"error": "..."}.
    """
    return _request(f"{BASE_URL}/git/locks/worktrees")


def health_check() -> bool:
    """Check if TRIX Git Arbiter is healthy.

    Returns:
        True if the server responds with HTTP 200, False otherwise.
    """
    resp = _request(f"{BASE_URL}/health")
    return "error" not in resp


def kiva_run(config: dict) -> dict:
    """Start a container via TRIX.

    Args:
        config: Container configuration (image, cpu, memory, etc.)

    Returns:
        JSON response with container details or {"error": "..."}.
    """
    return _request(f"{BASE_URL}/kiva-run", config)


def kiva_stop(container: str) -> dict:
    """Stop a container via TRIX.

    Args:
        container: Container name or ID.

    Returns:
        JSON response or {"error": "..."}.
    """
    return _request(f"{BASE_URL}/containers/{container}/stop")


def kiva_list() -> dict:
    """List all containers via TRIX.

    Returns:
        JSON response with containers list or {"error": "..."}.
    """
    return _request(f"{BASE_URL}/kiva-list")


def kiva_snapshot(container: str) -> dict:
    """Create a snapshot of a container via TRIX.

    Args:
        container: Container name or ID.

    Returns:
        JSON response with snapshot details or {"error": "..."}.
    """
    return _request(f"{BASE_URL}/containers/{container}/snapshot")


def kiva_restore(container: str, snapshot: str) -> dict:
    """Restore a container from snapshot via TRIX.

    Args:
        container: Container name or ID.
        snapshot: Snapshot name or ID.

    Returns:
        JSON response or {"error": "..."}.
    """
    return _request(f"{BASE_URL}/containers/{container}/restore", {"snapshot": snapshot})

