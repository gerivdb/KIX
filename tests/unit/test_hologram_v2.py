"""Tests for src/holograms/hologram_v2.py."""

from __future__ import annotations

import pytest

from src.holograms.hologram_v2 import get_arch_spec, get_platform_spec


class TestGetArchSpec:
    def test_x86_64(self):
        assert get_arch_spec("x86_64") == {"endian": "little", "bits": 64}

    def test_arm64(self):
        assert get_arch_spec("arm64") == {"endian": "little", "bits": 64}

    def test_unsupported_arch(self):
        with pytest.raises(ValueError):
            get_arch_spec("riscv")


class TestGetPlatformSpec:
    def test_linux(self):
        assert get_platform_spec("linux") == {"ext": "so", "sep": "/"}

    def test_windows(self):
        assert get_platform_spec("windows") == {"ext": "dll", "sep": "\\"}

    def test_macos(self):
        assert get_platform_spec("macos") == {"ext": "dylib", "sep": "/"}

    def test_unsupported_platform(self):
        with pytest.raises(ValueError):
            get_platform_spec("freebsd")
