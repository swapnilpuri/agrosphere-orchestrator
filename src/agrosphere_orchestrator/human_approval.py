"""Interactive Windows credential verification, isolated from business/state services.

No secret, password hash or reusable approval token is stored. Trusted administrators
control configuration and the database, as in the foundation threat model.
"""

import ctypes
import getpass
import os
import sys
from ctypes import wintypes
from typing import Protocol


class HumanVerifier(Protocol):
    def verify(self, subject: str, decision: str) -> str:
        """Confirm exact subject/decision, authenticate human, return canonical identity."""
        ...


def authenticate_windows(username: str, domain: str, password: str) -> str:
    if os.name != "nt":
        raise PermissionError("Windows credential verification is unavailable on this platform")
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    logon = advapi.LogonUserW
    logon.argtypes = [
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.HANDLE),
    ]
    logon.restype = wintypes.BOOL
    token = wintypes.HANDLE()
    if not logon(username, domain, password, 2, 0, ctypes.byref(token)):
        raise PermissionError("Human credential authentication failed")
    try:
        info = advapi.GetTokenInformation
        info.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            wintypes.LPVOID,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
        ]
        info.restype = wintypes.BOOL
        size = wintypes.DWORD()
        info(token, 1, None, 0, ctypes.byref(size))
        if not size.value:
            raise PermissionError("Cannot resolve authenticated identity")
        buffer = ctypes.create_string_buffer(size.value)
        if not info(token, 1, buffer, size, ctypes.byref(size)):
            raise PermissionError("Cannot resolve authenticated identity")
        sid = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_void_p))[0]
        convert = advapi.ConvertSidToStringSidW
        convert.argtypes = [ctypes.c_void_p, ctypes.POINTER(wintypes.LPWSTR)]
        convert.restype = wintypes.BOOL
        string = wintypes.LPWSTR()
        if not convert(sid, ctypes.byref(string)):
            raise PermissionError("Cannot resolve authenticated SID")
        try:
            return "sid:" + string.value
        finally:
            kernel.LocalFree.argtypes = [ctypes.c_void_p]
            kernel.LocalFree(ctypes.cast(string, ctypes.c_void_p))
    finally:
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel.CloseHandle(token)


class WindowsConsoleHumanVerifier:
    def verify(self, subject: str, decision: str) -> str:
        if os.name != "nt" or not sys.stdin.isatty():
            raise PermissionError(
                "Approval requires an interactive Windows human login; no --actor or automatic approval is accepted"
            )
        phrase = decision.upper() + " " + subject
        print("Review the exact scope/artifact digest, then type: " + phrase)
        if input("Decision: ").strip() != phrase:
            raise PermissionError("Exact approval subject was not confirmed")
        username = input("Windows username (or UPN): ").strip()
        domain = input("Windows domain (. for local, blank for UPN): ").strip() or None
        password = getpass.getpass("Windows password (never stored): ")
        if not password:
            raise PermissionError(
                "Password authentication is required; PIN-only accounts need a future identity adapter"
            )
        try:
            return authenticate_windows(username, domain, password)
        finally:
            password = ""
