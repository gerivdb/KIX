"""Tests pour les helpers JobObject de win32_process."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add shared-clients to path (same pattern as test_win32_process.py)
_shared_path = str(Path(__file__).resolve().parent.parent / "libs" / "shared-clients")
sys.path.insert(0, _shared_path)

from win32_process import (  # noqa: E402
    NtJobObject,
    assign_process_to_job,
    create_job_object,
    terminate_job,
)


class TestJobObjectHelpers:
    def test_create_job_object(self) -> None:
        with patch("win32_process.kernel32.CreateJobObjectW", return_value=1234):
            job = create_job_object("test-job")
        assert isinstance(job, NtJobObject)
        assert job.handle == 1234

    def test_assign_process_to_job_success(self) -> None:
        job = MagicMock(spec=NtJobObject)
        result = assign_process_to_job(job, 4242)
        assert result["ok"] is True
        assert result["pid"] == 4242
        job.assign_process.assert_called_once_with(4242)

    def test_assign_process_to_job_failure(self) -> None:
        job = MagicMock(spec=NtJobObject)
        job.assign_process.side_effect = OSError("assign failed")
        result = assign_process_to_job(job, 4242)
        assert result["ok"] is False
        assert "assign failed" in result["error"]

    def test_terminate_job_success(self) -> None:
        job = MagicMock(spec=NtJobObject)
        result = terminate_job(job, 1)
        assert result["ok"] is True
        assert result["exit_code"] == 1
        job.terminate.assert_called_once_with(1)

    def test_terminate_job_failure(self) -> None:
        job = MagicMock(spec=NtJobObject)
        job.terminate.side_effect = OSError("terminate failed")
        result = terminate_job(job, 1)
        assert result["ok"] is False
        assert "terminate failed" in result["error"]
