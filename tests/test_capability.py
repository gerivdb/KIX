"""Tests for KIX capability model."""

from src.capability import get_capabilities_for_role, check_capability


def test_admin_has_all_capabilities() -> None:
    capabilities = get_capabilities_for_role("admin")
    assert "runner:start" in capabilities
    assert "runner:stop" in capabilities
    assert "runner:restart" in capabilities
    assert "config:write" in capabilities
    assert "audit:write" in capabilities
    assert "remediation:trigger" in capabilities


def test_operator_has_operational_capabilities() -> None:
    capabilities = get_capabilities_for_role("operator")
    assert "runner:start" in capabilities
    assert "runner:stop" in capabilities
    assert "runner:restart" not in capabilities
    assert "config:write" not in capabilities
    assert "audit:write" not in capabilities


def test_viewer_has_read_only_capabilities() -> None:
    capabilities = get_capabilities_for_role("viewer")
    assert "runner:status" in capabilities
    assert "metrics:read" in capabilities
    assert "health:read" in capabilities
    assert "runner:start" not in capabilities
    assert "runner:stop" not in capabilities
    assert "config:write" not in capabilities


def test_check_capability_returns_true_for_allowed() -> None:
    assert check_capability("admin", "runner:start") is True
    assert check_capability("operator", "runner:start") is True
    assert check_capability("viewer", "runner:status") is True


def test_check_capability_returns_false_for_denied() -> None:
    assert check_capability("viewer", "runner:start") is False
    assert check_capability("operator", "runner:restart") is False
    assert check_capability("viewer", "config:write") is False


def test_check_capability_unknown_capability() -> None:
    assert check_capability("admin", "unknown:capability") is False
    assert check_capability("operator", "unknown:capability") is False
