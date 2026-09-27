"""Capability model for KIX role-based access control.

Maps RBAC roles to operational capabilities.
Source: unified-design/designs/kix/design.yaml capability_model.
"""

from __future__ import annotations

from typing import Literal

Role = Literal["admin", "operator", "viewer"]
Capability = str

# Capability definitions with required RBAC roles
_CAPABILITIES: dict[Capability, list[Role]] = {
    "runner:start": ["admin", "operator"],
    "runner:stop": ["admin", "operator"],
    "runner:restart": ["admin"],
    "runner:register": ["admin", "operator"],
    "runner:status": ["admin", "operator", "viewer"],
    "config:read": ["admin", "operator", "viewer"],
    "config:write": ["admin"],
    "audit:read": ["admin", "operator", "viewer"],
    "audit:write": ["admin"],
    "logs:read": ["admin", "operator", "viewer"],
    "metrics:read": ["admin", "operator", "viewer"],
    "health:read": ["admin", "operator", "viewer"],
    "remediation:trigger": ["admin", "operator"],
    "remediation:read": ["admin", "operator", "viewer"],
    "tlm:execute": ["admin"],
    "concurrency:manage": ["admin"],
    "process:track": ["admin", "operator", "viewer"],
    "process:restart": ["admin", "operator"],
    "pid:track": ["admin", "operator", "viewer"],
    "health:check": ["admin", "operator", "viewer"],
    "exe:launch": ["admin"],
    "swarm:read": ["admin", "operator", "viewer"],
    "alert:read": ["admin", "operator", "viewer"],
    "event:read": ["admin", "operator", "viewer"],
    "notification:read": ["admin", "operator", "viewer"],
    "dashboard:read": ["admin", "operator", "viewer"],
    "schedule:write": ["admin", "operator"],
    "schedule:read": ["admin", "operator", "viewer"],
}


def get_capabilities_for_role(role: Role) -> set[Capability]:
    """Return all capabilities granted to a role."""
    granted: set[Capability] = set()
    for capability, roles in _CAPABILITIES.items():
        if role in roles:
            granted.add(capability)
    return granted


def check_capability(role: Role, capability: Capability) -> bool:
    """Check if a role has a specific capability."""
    allowed_roles = _CAPABILITIES.get(capability, [])
    return role in allowed_roles
