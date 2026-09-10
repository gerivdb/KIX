#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Hologram API v2 — multi-architecture support (Phase 15).

Supports: x86_64, ARM64, Linux, Windows, macOS.

ERR_097-fix : created alongside swagger_ui_generator.py in CTULU/tools/.
"""

ARCHITECTURES = {
    "x86_64": {"endian": "little", "bits": 64},
    "arm64": {"endian": "little", "bits": 64},
    "aarch64": {"endian": "little", "bits": 64},
}

PLATFORMS = {
    "linux": {"ext": "so", "sep": "/"},
    "windows": {"ext": "dll", "sep": "\\"},
    "macos": {"ext": "dylib", "sep": "/"},
}


def get_arch_spec(arch: str) -> dict:
    """Return architecture spec or raise ValueError."""
    if arch not in ARCHITECTURES:
        raise ValueError(f"Unsupported arch: {arch}. Supported: {list(ARCHITECTURES.keys())}")
    return ARCHITECTURES[arch]


def get_platform_spec(platform: str) -> dict:
    """Return platform spec or raise ValueError."""
    if platform not in PLATFORMS:
        raise ValueError(f"Unsupported platform: {platform}. Supported: {list(PLATFORMS.keys())}")
    return PLATFORMS[platform]
