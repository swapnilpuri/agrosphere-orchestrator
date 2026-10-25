"""Conservative restart reconciliation; never infer success or replay a write."""

import ctypes
import os
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from .execution_models import ExecutionState
from .persistence import Execution, ExecutionAttempt, Run, Task, audit, now


def process_identity(pid: int) -> str | None:
    if os.name != "nt":
        return "UNKNOWN"  # Unknown identity is never proof that a process has exited.
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE, *([ctypes.POINTER(wintypes.FILETIME)] * 4)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.OpenProcess(0x1000, False, pid)
    if not handle:
        return "UNKNOWN" if ctypes.get_last_error() == 5 else None
    try:
        times = [wintypes.FILETIME() for _ in range(4)]
        if not kernel.GetProcessTimes(handle, *(ctypes.byref(t) for t in times)):
            return "UNKNOWN"
        return str((times[0].dwHighDateTime << 32) | times[0].dwLowDateTime)
    finally:
        kernel.CloseHandle(handle)


def extract_session(raw: str) -> str | None:
    import json

    for line in raw.splitlines():
        try:
            event = json.loads(line)
            if event.get("type") == "thread.started":
                return str(UUID(event["thread_id"]))
        except (ValueError, KeyError, AttributeError):
            continue
    return None


class CodexSessionManager:
    def __init__(self, engine):
        self.engine = engine

    def reconcile(self) -> list[dict]:
        from .execution import change

        findings = []
        with Session(self.engine) as session, session.begin():
            for execution in session.scalars(
                select(Execution).where(Execution.state.in_(["PREPARING", "RUNNING"]))
            ):
                attempts = list(
                    session.scalars(
                        select(ExecutionAttempt)
                        .where(ExecutionAttempt.execution_id == execution.id)
                        .order_by(ExecutionAttempt.created_at, ExecutionAttempt.id)
                    )
                )
                metadata = {}
                for attempt in attempts:
                    metadata.update(attempt.payload)
                owner, child = metadata.get("owner_pid"), metadata.get("pid")
                if (owner and process_identity(owner) == "UNKNOWN") or (
                    child and process_identity(child) == "UNKNOWN"
                ):
                    findings.append(
                        {
                            "execution": execution.id,
                            "state": execution.state,
                            "finding": "Process identity cannot be verified; recovery and replay remain blocked",
                        }
                    )
                    continue
                owner_matches = (
                    owner
                    and metadata.get("owner_identity")
                    and process_identity(owner) == metadata["owner_identity"]
                )
                child_matches = (
                    child
                    and metadata.get("process_identity")
                    and process_identity(child) == metadata["process_identity"]
                )
                if owner_matches or child_matches:
                    findings.append(
                        {
                            "execution": execution.id,
                            "state": execution.state,
                            "finding": "Recorded process identity is still alive; no replay or unconfirmed cancellation",
                        }
                    )
                    continue
                change(
                    session,
                    execution,
                    ExecutionState.INTERRUPTED,
                    {
                        "reason": "No matching live owner/process identity; partial worktree retained",
                        "partial_artifacts_preserved_in_place": True,
                    },
                )
                task = session.get(Task, execution.task_id)
                if task.state == "running":
                    task.state = "failed"
                    run = session.scalar(
                        select(Run).where(Run.task_id == task.id, Run.status == "running")
                    )
                    if run:
                        run.status, run.finished_at = "interrupted", now()
                    audit(
                        session,
                        task.id,
                        "task.interrupted",
                        "orchestrator",
                        {"execution_id": execution.id},
                    )
                findings.append({"execution": execution.id, "state": "INTERRUPTED"})
        return findings
