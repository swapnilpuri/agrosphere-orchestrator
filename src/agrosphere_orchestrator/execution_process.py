"""Shell-free process management, bounded capture and confirmed tree termination."""

import asyncio
import ctypes
import os
import re
import signal
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path


class Redactor:
    def __init__(self):
        self.secrets = [
            v
            for k, v in os.environ.items()
            if len(v) >= 6 and re.search(r"KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL", k, re.I)
        ]

    def clean(self, text: str) -> str:
        for value in sorted(self.secrets, key=len, reverse=True):
            text = text.replace(value, "[REDACTED]")
        text = re.sub(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+", r"\1[REDACTED]", text)
        text = re.sub(r"\bsk-[A-Za-z0-9_-]{10,}", "[REDACTED]", text)
        return re.sub(
            r'(?i)((?:password|api_key|access_token|refresh_token)["\s:=>]+)[^\s",}]+',
            r"\1[REDACTED]",
            text,
        )


def runtime_environment() -> dict[str, str]:
    allowed = {
        "PATH",
        "SYSTEMROOT",
        "SYSTEMDRIVE",
        "PROCESSOR_ARCHITECTURE",
        "OS",
        "WINDIR",
        "COMSPEC",
        "TEMP",
        "TMP",
        "USERPROFILE",
        "APPDATA",
        "LOCALAPPDATA",
        "HOMEDRIVE",
        "HOMEPATH",
        "PROGRAMFILES",
        "PROGRAMFILES(X86)",
        "CODEX_HOME",
    }
    env = {k: v for k, v in os.environ.items() if k.upper() in allowed}
    # Only the Codex credential is admitted; no cloud, database or production credentials.
    key = os.environ.get("CODEX_API_KEY")
    if key:
        env["CODEX_API_KEY"] = key
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_OPTIONAL_LOCKS"] = "0"
    return env


class WindowsJob:
    """Closing a job kills its remaining processes. Prompt is sent only after assignment."""

    def __init__(self, pid: int):
        from ctypes import wintypes

        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)

        class BASIC(ctypes.Structure):
            _fields_ = [
                ("ProcessTime", ctypes.c_int64),
                ("JobTime", ctypes.c_int64),
                ("Flags", wintypes.DWORD),
                ("Min", ctypes.c_size_t),
                ("Max", ctypes.c_size_t),
                ("Active", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t),
                ("Priority", wintypes.DWORD),
                ("Scheduling", wintypes.DWORD),
            ]

        class IO(ctypes.Structure):
            _fields_ = [
                (name, ctypes.c_uint64)
                for name in (
                    "ReadOps",
                    "WriteOps",
                    "OtherOps",
                    "ReadBytes",
                    "WriteBytes",
                    "OtherBytes",
                )
            ]

        class EXT(ctypes.Structure):
            _fields_ = [
                ("Basic", BASIC),
                ("Io", IO),
                ("ProcessMemory", ctypes.c_size_t),
                ("JobMemory", ctypes.c_size_t),
                ("PeakProcess", ctypes.c_size_t),
                ("PeakJob", ctypes.c_size_t),
            ]

        k = self.kernel
        k.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        k.CreateJobObjectW.restype = wintypes.HANDLE
        k.SetInformationJobObject.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            ctypes.c_void_p,
            wintypes.DWORD,
        ]
        k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        k.OpenProcess.restype = wintypes.HANDLE
        k.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        k.CloseHandle.argtypes = [wintypes.HANDLE]
        self.handle = k.CreateJobObjectW(None, None)
        limits = EXT()
        limits.Basic.Flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        process = None
        try:
            if not self.handle or not k.SetInformationJobObject(
                self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)
            ):
                raise OSError("Cannot configure bounded Windows job")
            process = k.OpenProcess(0x0100 | 0x0001, False, pid)
            if not process or not k.AssignProcessToJobObject(self.handle, process):
                raise OSError("Cannot assign Codex to a process-tree job")
        except Exception:
            self.close()
            raise
        finally:
            if process:
                k.CloseHandle(process)

    def close(self):
        if self.handle:
            self.kernel.CloseHandle(self.handle)
            self.handle = None


@dataclass
class ProcessOutcome:
    exit_code: int | None
    stdout: str
    stderr: str
    timed_out: bool = False
    cancelled: bool = False
    truncated: bool = False
    pid: int | None = None


class CodexProcessManager:
    def __init__(self, max_bytes: int = 2000000):
        self.max_bytes = max_bytes

    async def run(
        self,
        argv: list[str],
        cwd: Path,
        prompt: str,
        timeout: float,
        cancel_check=lambda: False,
        started=lambda pid: None,
    ) -> ProcessOutcome:
        kwargs = (
            {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
            if os.name == "nt"
            else {"start_new_session": True}
        )
        process = await asyncio.create_subprocess_exec(
            *argv,
            cwd=cwd,
            env=runtime_environment(),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            **kwargs,
        )
        job = None
        timed_out = cancelled = truncated = False
        total = 0

        async def collect(stream):
            nonlocal total, truncated
            chunks = []
            while data := await stream.read(8192):
                available = max(0, self.max_bytes - total)
                chunks.append(data[:available])
                total += len(data)
                if total > self.max_bytes:
                    truncated = True
            return b"".join(chunks).decode("utf-8", errors="replace")

        readers = [
            asyncio.create_task(collect(process.stdout)),
            asyncio.create_task(collect(process.stderr)),
        ]
        try:
            if os.name == "nt":
                job = WindowsJob(process.pid)
            started(process.pid)
            process.stdin.write(prompt.encode("utf-8"))
            await process.stdin.drain()
            process.stdin.close()
            deadline = time.monotonic() + timeout
            while process.returncode is None:
                cancelled = bool(cancel_check())
                timed_out = time.monotonic() >= deadline
                if cancelled or timed_out or truncated:
                    if job:
                        job.close()
                    elif os.name != "nt":
                        os.killpg(process.pid, signal.SIGKILL)
                    else:
                        process.kill()
                    break
                await asyncio.sleep(0.1)
            await asyncio.wait_for(process.wait(), timeout=10)
            stdout, stderr = await asyncio.wait_for(asyncio.gather(*readers), timeout=10)
            return ProcessOutcome(
                process.returncode, stdout, stderr, timed_out, cancelled, truncated, process.pid
            )
        finally:
            if job:
                job.close()
            if process.returncode is None:
                process.kill()
                await process.wait()
            for reader in readers:
                if not reader.done():
                    reader.cancel()
