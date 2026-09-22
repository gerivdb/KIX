"""Tests win32_process module."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add shared-clients to path (same pattern as existing tests)
_shared_path = str(Path(__file__).resolve().parent.parent / "libs" / "shared-clients")
sys.path.insert(0, _shared_path)

from win32_process import (
    NtJobObject,
    get_current_pid,
    open_process,
    terminate_process,
)


class TestWin32Process:
    def test_get_current_pid(self):
        pid = get_current_pid()
        assert isinstance(pid, int)
        assert pid > 0

    def test_open_process_self(self):
        pid = get_current_pid()
        handle = open_process(pid)
        assert handle is not None
        assert isinstance(handle, int)

    def test_open_process_invalid(self):
        handle = open_process(-1)
        assert handle is None

    def test_terminate_process_invalid(self):
        result = terminate_process(-1)
        assert result["ok"] is False


class TestNtJobObject:
    def test_create_and_terminate(self):
        job = NtJobObject()
        assert job.handle != 0
        job.terminate(0)

    def test_set_memory_limit(self):
        job = NtJobObject()
        try:
            job.set_memory_limit(1024 * 1024 * 1024)  # 1 Go
        except PermissionError:
            pytest.skip("SetInformationJobObject requires admin privileges")
        job.terminate(0)

    def test_get_process_count(self):
        job = NtJobObject()
        count = job.get_process_count()
        assert isinstance(count, int)
        job.terminate(0)
