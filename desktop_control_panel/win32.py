"""Small, dependency-free Win32 helpers used by the control panel.

Only stable Windows APIs are wrapped here.  Keeping this module behind a
small interface makes the service lifecycle testable without PowerShell,
pywin32, or a tray library.
"""

from __future__ import annotations

import ctypes
import os
import time
from ctypes import wintypes
from pathlib import Path
from typing import Final


if os.name != "nt":  # pragma: no cover - the shipped control panel is Windows-only
    raise RuntimeError("The Windows control panel can only run on Windows.")


kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
user32 = ctypes.WinDLL("user32", use_last_error=True)

DWORD = wintypes.DWORD
HANDLE = wintypes.HANDLE
BOOL = wintypes.BOOL
LPVOID = wintypes.LPVOID
SIZE_T = ctypes.c_size_t
ULONG_PTR = ctypes.c_size_t

ERROR_ALREADY_EXISTS: Final = 183
ERROR_FILE_NOT_FOUND: Final = 2
ERROR_INSUFFICIENT_BUFFER: Final = 122
WAIT_OBJECT_0: Final = 0
WAIT_TIMEOUT: Final = 258
INFINITE: Final = 0xFFFFFFFF
EVENT_MODIFY_STATE: Final = 0x0002
SYNCHRONIZE: Final = 0x00100000
PROCESS_TERMINATE: Final = 0x0001
PROCESS_QUERY_LIMITED_INFORMATION: Final = 0x1000
PROCESS_SET_QUOTA: Final = 0x0100
TH32CS_SNAPPROCESS: Final = 0x00000002
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE: Final = 0x00002000
JobObjectExtendedLimitInformation: Final = 9
SW_RESTORE: Final = 9
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value


class Win32Error(OSError):
    """A Win32 call failed."""


def _raise_last_error(action: str) -> None:
    error = ctypes.get_last_error()
    raise Win32Error(error, f"{action} failed: {ctypes.FormatError(error).strip()}")


kernel32.CloseHandle.argtypes = [HANDLE]
kernel32.CloseHandle.restype = BOOL
kernel32.CreateMutexW.argtypes = [LPVOID, BOOL, wintypes.LPCWSTR]
kernel32.CreateMutexW.restype = HANDLE
kernel32.OpenMutexW.argtypes = [DWORD, BOOL, wintypes.LPCWSTR]
kernel32.OpenMutexW.restype = HANDLE
kernel32.CreateEventW.argtypes = [LPVOID, BOOL, BOOL, wintypes.LPCWSTR]
kernel32.CreateEventW.restype = HANDLE
kernel32.OpenEventW.argtypes = [DWORD, BOOL, wintypes.LPCWSTR]
kernel32.OpenEventW.restype = HANDLE
kernel32.SetEvent.argtypes = [HANDLE]
kernel32.SetEvent.restype = BOOL
kernel32.WaitForSingleObject.argtypes = [HANDLE, DWORD]
kernel32.WaitForSingleObject.restype = DWORD
kernel32.OpenProcess.argtypes = [DWORD, BOOL, DWORD]
kernel32.OpenProcess.restype = HANDLE
kernel32.QueryFullProcessImageNameW.argtypes = [
    HANDLE,
    DWORD,
    wintypes.LPWSTR,
    ctypes.POINTER(DWORD),
]
kernel32.QueryFullProcessImageNameW.restype = BOOL
kernel32.TerminateProcess.argtypes = [HANDLE, wintypes.UINT]
kernel32.TerminateProcess.restype = BOOL
kernel32.CreateJobObjectW.argtypes = [LPVOID, wintypes.LPCWSTR]
kernel32.CreateJobObjectW.restype = HANDLE
kernel32.SetInformationJobObject.argtypes = [HANDLE, ctypes.c_int, LPVOID, DWORD]
kernel32.SetInformationJobObject.restype = BOOL
kernel32.AssignProcessToJobObject.argtypes = [HANDLE, HANDLE]
kernel32.AssignProcessToJobObject.restype = BOOL
kernel32.TerminateJobObject.argtypes = [HANDLE, wintypes.UINT]
kernel32.TerminateJobObject.restype = BOOL
kernel32.CreateToolhelp32Snapshot.argtypes = [DWORD, DWORD]
kernel32.CreateToolhelp32Snapshot.restype = HANDLE
user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user32.ShowWindow.restype = BOOL
user32.SetForegroundWindow.argtypes = [wintypes.HWND]
user32.SetForegroundWindow.restype = BOOL


class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_longlong),
        ("PerJobUserTimeLimit", ctypes.c_longlong),
        ("LimitFlags", DWORD),
        ("MinimumWorkingSetSize", SIZE_T),
        ("MaximumWorkingSetSize", SIZE_T),
        ("ActiveProcessLimit", DWORD),
        ("Affinity", ULONG_PTR),
        ("PriorityClass", DWORD),
        ("SchedulingClass", DWORD),
    ]


class IO_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("ReadOperationCount", ctypes.c_ulonglong),
        ("WriteOperationCount", ctypes.c_ulonglong),
        ("OtherOperationCount", ctypes.c_ulonglong),
        ("ReadTransferCount", ctypes.c_ulonglong),
        ("WriteTransferCount", ctypes.c_ulonglong),
        ("OtherTransferCount", ctypes.c_ulonglong),
    ]


class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
        ("IoInfo", IO_COUNTERS),
        ("ProcessMemoryLimit", SIZE_T),
        ("JobMemoryLimit", SIZE_T),
        ("PeakProcessMemoryUsed", SIZE_T),
        ("PeakJobMemoryUsed", SIZE_T),
    ]


MAX_PATH = 260


class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", DWORD),
        ("cntUsage", DWORD),
        ("th32ProcessID", DWORD),
        ("th32DefaultHeapID", ULONG_PTR),
        ("th32ModuleID", DWORD),
        ("cntThreads", DWORD),
        ("th32ParentProcessID", DWORD),
        ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", DWORD),
        ("szExeFile", wintypes.WCHAR * MAX_PATH),
    ]


kernel32.Process32FirstW.argtypes = [HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
kernel32.Process32FirstW.restype = BOOL
kernel32.Process32NextW.argtypes = [HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
kernel32.Process32NextW.restype = BOOL


def close_handle(handle: int | None) -> None:
    if handle:
        kernel32.CloseHandle(handle)


def normalize_windows_path(path: str | Path) -> str:
    return os.path.normcase(os.path.normpath(os.path.abspath(str(path))))


def paths_match(left: str | Path, right: str | Path) -> bool:
    return normalize_windows_path(left) == normalize_windows_path(right)


class NamedMutex:
    """A named mutex that identifies one control panel per package directory."""

    def __init__(self, name: str) -> None:
        ctypes.set_last_error(0)
        handle = kernel32.CreateMutexW(None, False, name)
        if not handle:
            _raise_last_error("CreateMutexW")
        self.name = name
        self.handle: int | None = handle
        self.already_exists = ctypes.get_last_error() == ERROR_ALREADY_EXISTS

    def close(self) -> None:
        close_handle(self.handle)
        self.handle = None

    def __enter__(self) -> "NamedMutex":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


class NamedAutoResetEvent:
    """A locally scoped named auto-reset event."""

    def __init__(self, name: str) -> None:
        handle = kernel32.CreateEventW(None, False, False, name)
        if not handle:
            _raise_last_error("CreateEventW")
        self.name = name
        self.handle: int | None = handle

    def is_set(self) -> bool:
        if not self.handle:
            return False
        result = kernel32.WaitForSingleObject(self.handle, 0)
        if result == WAIT_OBJECT_0:
            return True
        if result == WAIT_TIMEOUT:
            return False
        _raise_last_error("WaitForSingleObject")
        return False

    def close(self) -> None:
        close_handle(self.handle)
        self.handle = None

    def __enter__(self) -> "NamedAutoResetEvent":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def signal_named_event(name: str) -> bool:
    handle = kernel32.OpenEventW(EVENT_MODIFY_STATE, False, name)
    if not handle:
        if ctypes.get_last_error() == ERROR_FILE_NOT_FOUND:
            return False
        _raise_last_error("OpenEventW")
    try:
        if not kernel32.SetEvent(handle):
            _raise_last_error("SetEvent")
        return True
    finally:
        close_handle(handle)


def named_mutex_exists(name: str) -> bool:
    handle = kernel32.OpenMutexW(SYNCHRONIZE, False, name)
    if not handle:
        if ctypes.get_last_error() == ERROR_FILE_NOT_FOUND:
            return False
        _raise_last_error("OpenMutexW")
    close_handle(handle)
    return True


def wait_for_named_mutex_release(name: str, timeout_seconds: float) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if not named_mutex_exists(name):
            return True
        time.sleep(0.1)
    return not named_mutex_exists(name)


def get_process_image_path(process_id: int) -> Path | None:
    if process_id <= 0:
        return None
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, process_id)
    if not handle:
        return None
    try:
        size = MAX_PATH
        while size <= 32768:
            buffer = ctypes.create_unicode_buffer(size)
            length = DWORD(size)
            if kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(length)):
                return Path(buffer.value)
            if ctypes.get_last_error() != ERROR_INSUFFICIENT_BUFFER:
                return None
            size *= 2
        return None
    finally:
        close_handle(handle)


def process_matches_executable(process_id: int, executable: str | Path) -> bool:
    actual_path = get_process_image_path(process_id)
    return actual_path is not None and paths_match(actual_path, executable)


def terminate_process(process_id: int, timeout_ms: int = 5000) -> bool:
    handle = kernel32.OpenProcess(PROCESS_TERMINATE | SYNCHRONIZE, False, process_id)
    if not handle:
        return False
    try:
        if not kernel32.TerminateProcess(handle, 1):
            return False
        return kernel32.WaitForSingleObject(handle, timeout_ms) == WAIT_OBJECT_0
    finally:
        close_handle(handle)


def _process_parent_map() -> dict[int, list[int]]:
    snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snapshot == INVALID_HANDLE_VALUE:
        _raise_last_error("CreateToolhelp32Snapshot")
    parents: dict[int, list[int]] = {}
    try:
        entry = PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
        has_entry = kernel32.Process32FirstW(snapshot, ctypes.byref(entry))
        while has_entry:
            parents.setdefault(int(entry.th32ParentProcessID), []).append(int(entry.th32ProcessID))
            entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
            has_entry = kernel32.Process32NextW(snapshot, ctypes.byref(entry))
    finally:
        close_handle(snapshot)
    return parents


def is_process_descendant(process_id: int, ancestor_process_id: int) -> bool:
    if process_id <= 0 or ancestor_process_id <= 0:
        return False
    if process_id == ancestor_process_id:
        return True

    parents = _process_parent_map()
    pending = [ancestor_process_id]
    seen = {ancestor_process_id}
    while pending:
        parent = pending.pop()
        for child in parents.get(parent, []):
            if child == process_id:
                return True
            if child > 0 and child not in seen:
                seen.add(child)
                pending.append(child)
    return False


def terminate_process_tree(process_id: int, expected_executable: str | Path) -> bool:
    """Terminate an owned process and its current descendants as a safe fallback.

    Normal control-panel shutdown uses a Job Object.  This fallback is only
    used to clean a state file left by an interrupted earlier release.
    """

    if not process_matches_executable(process_id, expected_executable):
        return False

    parents = _process_parent_map()
    descendants: list[int] = []
    pending = [process_id]
    seen = {process_id}
    while pending:
        parent = pending.pop()
        for child in parents.get(parent, []):
            if child > 0 and child not in seen:
                seen.add(child)
                descendants.append(child)
                pending.append(child)

    success = True
    for target_pid in reversed(descendants):
        terminate_process(target_pid)
    success = terminate_process(process_id) and success
    return success


class JobObject:
    """Owns a backend process tree and kills it when the panel exits."""

    def __init__(self) -> None:
        handle = kernel32.CreateJobObjectW(None, None)
        if not handle:
            _raise_last_error("CreateJobObjectW")

        information = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        information.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not kernel32.SetInformationJobObject(
            handle,
            JobObjectExtendedLimitInformation,
            ctypes.byref(information),
            ctypes.sizeof(information),
        ):
            close_handle(handle)
            _raise_last_error("SetInformationJobObject")

        self.handle: int | None = handle

    def assign_process(self, process_id: int) -> None:
        if not self.handle:
            raise RuntimeError("Job Object has already been closed.")
        process_handle = kernel32.OpenProcess(
            PROCESS_SET_QUOTA | PROCESS_TERMINATE | PROCESS_QUERY_LIMITED_INFORMATION,
            False,
            process_id,
        )
        if not process_handle:
            _raise_last_error("OpenProcess")
        try:
            if not kernel32.AssignProcessToJobObject(self.handle, process_handle):
                _raise_last_error("AssignProcessToJobObject")
        finally:
            close_handle(process_handle)

    def assign_current_process(self) -> None:
        self.assign_process(os.getpid())

    def terminate(self) -> bool:
        if not self.handle:
            return True
        if not kernel32.TerminateJobObject(self.handle, 1):
            return False
        return True

    def close(self) -> None:
        close_handle(self.handle)
        self.handle = None

    def __enter__(self) -> "JobObject":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def restore_and_focus_window(window_handle: int) -> None:
    if not window_handle:
        return
    user32.ShowWindow(wintypes.HWND(window_handle), SW_RESTORE)
    user32.SetForegroundWindow(wintypes.HWND(window_handle))
