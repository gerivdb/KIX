"""Win32 Process Helpers — module partagé KIX/LOOPX/TRIX.

Couvre P1 du PRD-MOC GEN-041 :
- OpenProcess / TerminateProcess / handles Win32
- NT Job Objects (extrait de TRIX nt_job_arbiter.py)
- Fingerprint d'instance via /health

Ce module est volontairement minimaliste : pas de dépendance externe,
pas de logique métier, seulement des primitives Win32 testables.
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes
import logging
import os
import sys
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Kernel32 bindings
# ---------------------------------------------------------------------------

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

OpenProcess = kernel32.OpenProcess
OpenProcess.restype = ctypes.wintypes.HANDLE
OpenProcess.argtypes = [ctypes.wintypes.DWORD, ctypes.wintypes.BOOL, ctypes.wintypes.DWORD]

TerminateProcess = kernel32.TerminateProcess
TerminateProcess.restype = ctypes.wintypes.BOOL
TerminateProcess.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.UINT]

CloseHandle = kernel32.CloseHandle
CloseHandle.restype = ctypes.wintypes.BOOL
CloseHandle.argtypes = [ctypes.wintypes.HANDLE]

GetCurrentProcessId = kernel32.GetCurrentProcessId
GetCurrentProcessId.restype = ctypes.wintypes.DWORD

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
PROCESS_TERMINATE = 0x0001

# ---------------------------------------------------------------------------
# Helpers processus Win32
# ---------------------------------------------------------------------------

def open_process(pid: int, access: int = PROCESS_QUERY_LIMITED_INFORMATION) -> Optional[int]:
    """Ouvre un handle sur un processus. Retourne un IntPtr (ou None)."""
    handle = OpenProcess(access, False, pid)
    if not handle:
        return None
    return int(handle)


def terminate_process(pid: int, force: bool = True) -> dict:
    """Termine un processus par PID via Win32 API."""
    access = PROCESS_TERMINATE
    handle = open_process(pid, access)
    if handle is None:
        return {"ok": False, "pid": pid, "error": "OpenProcess failed"}
    try:
        ok = TerminateProcess(handle, 1 if force else 0)
        return {
            "ok": bool(ok),
            "pid": pid,
            "exit_code": 1 if force else 0,
        }
    except Exception as exc:
        return {"ok": False, "pid": pid, "error": str(exc)}
    finally:
        CloseHandle(handle)


def get_current_pid() -> int:
    """Retourne le PID du processus courant."""
    return GetCurrentProcessId()


# ---------------------------------------------------------------------------
# NT Job Objects (extrait TRIX nt_job_arbiter.py)
# ---------------------------------------------------------------------------

class NtJobObject:
    """Wrapper NT Job Object pour isolation RAM/CPU (ADR-106)."""

    JOB_OBJECT_LIMIT_PROCESS_MEMORY = 0x00000100
    JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9

    def __init__(self, name: str | None = None) -> None:
        self._handle = kernel32.CreateJobObjectW(None, name)
        if not self._handle:
            raise ctypes.WinError(ctypes.get_last_error())

    def set_memory_limit(self, limit_bytes: int) -> None:
        """Définit la limite mémoire pour ce job."""
        class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("BasicLimitInformation", ctypes.c_byte * 48),
                ("IoInfo", ctypes.c_byte * 48),
                ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t),
                ("PeakJobMemoryUsed", ctypes.c_size_t),
            ]

        info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        info.LimitFlags = self.JOB_OBJECT_LIMIT_PROCESS_MEMORY
        info.ProcessMemoryLimit = limit_bytes
        info.JobMemoryLimit = limit_bytes
        ok = kernel32.SetInformationJobObject(
            self._handle,
            self.JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
            ctypes.byref(info),
            ctypes.sizeof(info),
        )
        if not ok:
            raise ctypes.WinError(ctypes.get_last_error())

    def assign_process(self, pid: int) -> None:
        """Attache un processus au job."""
        process_handle = OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not process_handle:
            raise ctypes.WinError(ctypes.get_last_error())
        ok = kernel32.AssignProcessToJobObject(self._handle, process_handle)
        kernel32.CloseHandle(process_handle)
        if not ok:
            raise ctypes.WinError(ctypes.get_last_error())

    def terminate(self, exit_code: int = 1) -> None:
        """Termine tous les processus du job et ferme le handle."""
        kernel32.TerminateJobObject(self._handle, exit_code)
        kernel32.CloseHandle(self._handle)

    def get_process_count(self) -> int:
        """Retourne le nombre de processus actifs dans le job."""
        class JOBOBJECT_BASIC_PROCESS_ID_LIST(ctypes.Structure):
            _fields_ = [
                ("NumberOfAssignedProcesses", ctypes.c_uint32),
                ("NumberOfProcessIdsInList", ctypes.c_uint32),
                ("ProcessIdList", ctypes.c_uint32 * 1),
            ]

        buf = ctypes.create_string_buffer(ctypes.sizeof(JOBOBJECT_BASIC_PROCESS_ID_LIST))
        result = kernel32.QueryInformationJobObject(
            self._handle,
            3,  # JobObjectBasicProcessIdList
            buf,
            ctypes.sizeof(buf),
            None,
        )
        if not result:
            return 0
        info = ctypes.cast(buf, ctypes.POINTER(JOBOBJECT_BASIC_PROCESS_ID_LIST)).contents
        return info.NumberOfAssignedProcesses

    @property
    def handle(self) -> int:
        return int(self._handle)
