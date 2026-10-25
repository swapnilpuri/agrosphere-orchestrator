"""Explicit single-task orchestration. No scheduler, automatic retries or multi-agent loop."""

import asyncio
import json
import logging
import os
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from .codex_runtime import CodexExecutor, executable, parse_output, permission_arguments
from .configuration import ApprovalPolicy, load_yaml
from .design import canonical
from .design_artifacts import digest
from .execution_context import assemble_prompt, build_context
from .execution_models import (
    ExecutionError,
    ExecutionMode,
    ExecutionPolicy,
    ExecutionRequest,
    ExecutionResult,
    ExecutionState,
)
from .execution_process import CodexProcessManager, Redactor
from .execution_workspace import (
    check_changes,
    create_worktree,
    preserve,
    probe_isolation,
    tree_fingerprints,
)
from .persistence import Execution, ExecutionAttempt, ExecutionGrant, Run, Task, audit, now
from .state import transition

E = ExecutionState
TERMINAL = {E.SUCCEEDED, E.FAILED, E.TIMED_OUT, E.CANCELLED, E.INTERRUPTED}
EDGES = {
    E.QUEUED: {E.AWAITING_APPROVAL, E.CANCELLED},
    E.AWAITING_APPROVAL: {E.PREPARING, E.CANCELLED},
    E.PREPARING: {E.RUNNING, E.FAILED, E.INTERRUPTED, E.CANCELLED},
    E.RUNNING: TERMINAL,
}


def request_digest(request: ExecutionRequest) -> str:
    return digest(canonical(request.model_dump(mode="json", exclude={"approval_reference"})))


def change(session, execution, state, payload=None):
    state = E(state)
    if state != E(execution.state) and state not in EDGES.get(E(execution.state), set()):
        raise ValueError(f"Invalid execution transition {execution.state} -> {state}")
    execution.state = state.value
    execution.active_slot = 1 if state in {E.PREPARING, E.RUNNING} else None
    execution.updated_at = now()
    session.add(
        ExecutionAttempt(
            id=str(uuid4()), execution_id=execution.id, state=state.value, payload=payload or {}
        )
    )
    audit(
        session,
        execution.id,
        "execution.transitioned",
        "orchestrator",
        {"state": state.value, **(payload or {})},
    )


def execution_directory(settings, identity: str) -> Path:
    root = settings.execution_root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    directory = (root / identity).resolve()
    if directory.parent != root or directory.is_symlink():
        raise PermissionError("Execution directory escaped configured private root")
    directory.mkdir(exist_ok=True)
    return directory


def queue_execution(
    engine,
    settings,
    task_id: str,
    mode=ExecutionMode.READ_ONLY,
    scopes=None,
    specialization=None,
    command_ids=None,
    timeout=300,
    parent=None,
    instructions=None,
    continuation=None,
) -> str:
    mode = ExecutionMode(mode)
    scopes, command_ids = scopes or ["."], command_ids or []
    with Session(engine) as session, session.begin():
        if mode == ExecutionMode.VALIDATION_ONLY and not command_ids:
            raise PermissionError(
                "Validation-only execution requires allowlisted validation commands"
            )
        if continuation and mode != ExecutionMode.READ_ONLY:
            raise PermissionError("Only verified read-only sessions may continue")
        context, context_hash, task, milestone = build_context(
            session, settings, task_id, mode, scopes, specialization, command_ids, parent
        )
        if task.state not in {"pending", "ready", "failed"}:
            raise PermissionError(
                "Task is active or completed; an explicit recovery review is required"
            )
        if session.scalar(
            select(Execution).where(
                Execution.task_id == task.id,
                Execution.state.in_(
                    [E.QUEUED.value, E.AWAITING_APPROVAL.value, E.PREPARING.value, E.RUNNING.value]
                ),
            )
        ):
            raise PermissionError("Task already has an outstanding execution")
        policy = ExecutionPolicy.model_validate(context["policy"])
        if timeout > policy.timeout_limit_seconds:
            raise PermissionError("Requested timeout exceeds execution policy")
        identity = str(uuid4())
        path = (
            str((settings.execution_root.resolve() / identity / "worktree").resolve())
            if mode != ExecutionMode.READ_ONLY
            else context["repository"]["path"]
        )
        request = ExecutionRequest(
            project_id=milestone.project_id,
            milestone_id=milestone.external_id,
            task_id=task.id,
            agent_role=task.spec["role"],
            specialization=specialization,
            repository=task.spec["repository"],
            worktree_path=path,
            allowed_file_scopes=scopes,
            required_input_artifacts=context["artifacts"],
            instructions=Redactor().clean(instructions or task.spec["title"]),
            role_instructions=context["role"]["system_instructions"]
            + "\n"
            + context["role"].get("specialization_instructions", {}).get(specialization, ""),
            acceptance_criteria=task.spec["acceptance_criteria"],
            mode=mode,
            timeout_seconds=timeout,
            validation_commands=command_ids,
            source_head=context["repository"]["head"],
            context_digest=context_hash,
            design_revision=context["design_revision"],
            parent_execution_id=parent,
            continuation_session_id=continuation,
        )
        execution = Execution(
            id=identity,
            task_id=task.id,
            state=E.QUEUED.value,
            request=request.model_dump(mode="json"),
            context=context,
            cancel_requested=False,
        )
        session.add(execution)
        session.flush()
        change(session, execution, E.AWAITING_APPROVAL, {"request_digest": request_digest(request)})
    return identity


def approve_execution(engine, settings, identity: str, verifier, expiry_seconds=900) -> str:
    if not settings.execution_approvers or not 1 <= expiry_seconds <= 3600:
        raise PermissionError("Authorized execution approvers and a bounded expiry are required")
    with Session(engine) as session:
        execution = session.get(Execution, identity)
        if execution is None or execution.state != E.AWAITING_APPROVAL:
            raise ValueError("Execution is not awaiting approval")
        request = ExecutionRequest.model_validate(execution.request)
        expected = request_digest(request)
    actor = verifier.verify(identity + ":execute:" + expected, "approved")
    if actor not in settings.execution_approvers:
        raise PermissionError("Authenticated identity is not an execution approver")
    with Session(engine) as session, session.begin():
        execution = session.get(Execution, identity)
        current = ExecutionRequest.model_validate(execution.request)
        if execution.state != E.AWAITING_APPROVAL or request_digest(current) != expected:
            raise ValueError("Execution scope changed during approval")
        grant = ExecutionGrant(
            id=str(uuid4()),
            execution_id=identity,
            request_digest=expected,
            actor=actor,
            expires_at=(datetime.now(UTC) + timedelta(seconds=expiry_seconds)).isoformat(),
        )
        session.add(grant)
        current.approval_reference = grant.id
        execution.request = current.model_dump(mode="json")
        audit(
            session,
            identity,
            "execution.approved",
            actor,
            {"grant_id": grant.id, "digest": expected, "expires_at": grant.expires_at},
        )
        return grant.id


def check_grant(session, execution, settings):
    request = ExecutionRequest.model_validate(execution.request)
    grant = (
        session.get(ExecutionGrant, request.approval_reference)
        if request.approval_reference
        else None
    )
    if (
        grant is None
        or grant.execution_id != execution.id
        or grant.actor not in settings.execution_approvers
    ):
        raise PermissionError("Authenticated execution approval is missing or revoked")
    if grant.request_digest != request_digest(request) or datetime.fromisoformat(
        grant.expires_at
    ) <= datetime.now(UTC):
        raise PermissionError("Execution grant changed or expired")
    return request, grant


def cancel_requested(engine, identity):
    with Session(engine) as session:
        execution = session.get(Execution, identity)
        return execution is None or execution.cancel_requested


def cancel_execution(engine, identity):
    with Session(engine) as session, session.begin():
        execution = session.get(Execution, identity)
        if execution is None:
            raise ValueError("Unknown execution")
        if E(execution.state) in TERMINAL:
            return execution.state
        execution.cancel_requested = True
        audit(session, identity, "execution.cancel.requested", "local-user", {})
        if E(execution.state) in {E.QUEUED, E.AWAITING_APPROVAL}:
            change(
                session,
                execution,
                E.CANCELLED,
                {"confirmed": True, "reason": "No process was started"},
            )
        return execution.state


def record_started(engine, identity, pid):
    with Session(engine) as session, session.begin():
        execution = session.get(Execution, identity)
        if execution.state == E.PREPARING:
            from .execution_sessions import process_identity

            change(
                session,
                execution,
                E.RUNNING,
                {
                    "pid": pid,
                    "owner_pid": os.getpid(),
                    "owner_identity": process_identity(os.getpid()),
                    "process_identity": process_identity(pid),
                    "started_at": now(),
                },
            )


def store_report(settings, identity, result):
    directory = execution_directory(settings, identity)
    (directory / "result.json").write_text(result.model_dump_json(indent=2), encoding="utf-8")
    text = (
        f"# Execution {identity}\n\nStatus: {result.status}\nRole: {result.agent_role}\n"
        f"Task: {result.task_id}\nDuration: {result.duration_seconds:.3f}s\n\n{result.summary}\n\n"
        f"Implementation verified by orchestrator: {result.implementation_verified}\n\n"
        "## Changed files\n\n" + "\n".join(f"- {p}" for p in result.changed_files) + "\n\n"
        "## Validation\n\n" + json.dumps(result.validation_results, indent=2) + "\n\n"
        "## Evidence\n\n" + "\n".join(f"- {p}" for p in result.evidence_references)
    )
    if result.output:
        for label, entries in (
            ("Work performed", result.output.work_performed),
            ("Model-reported commands", result.output.commands_executed),
            ("Errors", result.output.errors),
            ("Warnings", result.output.warnings),
            ("Unresolved issues", result.output.unresolved_issues),
            ("Suggested next actions", result.output.suggested_next_actions),
        ):
            text += "\n\n## " + label + "\n\n" + "\n".join("- " + s for s in entries)
    text += "\n\n## Execution metadata\n\n" + json.dumps(
        {
            "started_at": result.started_at,
            "ended_at": result.ended_at,
            "session_id": result.session_id,
            "exit_code": result.exit_code,
            "error": result.error.model_dump() if result.error else None,
            "usage": result.usage,
            "estimated_cost": result.estimated_cost,
        },
        indent=2,
    )
    (directory / "REPORT.md").write_text(text + "\n", encoding="utf-8")


async def run_execution(
    engine, settings, identity: str, adapter=None, isolation_probe=probe_isolation
):
    policy = load_yaml(settings.execution_policy, ExecutionPolicy)
    if adapter is None and settings.codex_transport == "mcp":
        raise PermissionError(
            "Installed MCP transport lacks certified granular isolation; select auto/exec"
        )
    adapter = adapter or CodexExecutor(settings, CodexProcessManager(policy.max_log_bytes))
    if not policy.live_enabled:
        raise PermissionError("Live execution is disabled in execution policy")
    with Session(engine) as session, session.begin():
        execution = session.get(Execution, identity)
        if execution is None or E(execution.state) != E.AWAITING_APPROVAL:
            raise PermissionError("Execution is not an unconsumed approved request")
        request, grant = check_grant(session, execution, settings)
        context, current_hash, task, _ = build_context(
            session,
            settings,
            request.task_id,
            request.mode,
            request.allowed_file_scopes,
            request.specialization,
            request.validation_commands,
            request.parent_execution_id,
        )
        if current_hash != request.context_digest or context != execution.context:
            raise PermissionError(
                "Context/design/role/policy changed after assembly; requeue and reapprove"
            )
        if session.scalar(
            select(Execution).where(
                Execution.id != identity, Execution.state.in_([E.PREPARING.value, E.RUNNING.value])
            )
        ):
            raise PermissionError("AEO-2 supports one active execution only")
        from .execution_sessions import process_identity

        change(
            session,
            execution,
            E.PREPARING,
            {
                "grant_id": grant.id,
                "owner_pid": os.getpid(),
                "owner_identity": process_identity(os.getpid()),
            },
        )
    directory = execution_directory(settings, identity)
    started_at, clock = now(), time.monotonic()
    source = Path(context["repository"]["path"])
    cwd = Path(request.worktree_path)
    before = {}
    outcome = None
    evidence, validation, changes = [], [], []
    result_state, error, output, session_id, usage = E.FAILED, None, None, None, {}
    task_started = False
    try:
        if request.mode != ExecutionMode.READ_ONLY:
            branch = create_worktree(source, cwd, identity, request.source_head)
            (directory / "workspace.json").write_text(
                json.dumps(
                    {
                        "source": str(source),
                        "path": str(cwd),
                        "head": request.source_head,
                        "branch": branch,
                    }
                ),
                encoding="utf-8",
            )
        before = tree_fingerprints(cwd, policy.max_artifact_bytes)
        # Native canary must pass before task state changes or any model invocation.
        permissions = permission_arguments(request) if isolation_probe is probe_isolation else []
        probe = await asyncio.to_thread(
            isolation_probe, executable(settings), request, permissions, directory
        )
        (directory / "isolation.json").write_text(json.dumps(probe, indent=2), encoding="utf-8")
        evidence.append(str(directory / "isolation.json"))
        with Session(engine) as session:
            execution = session.get(Execution, identity)
            check_grant(session, execution, settings)
            _, rechecked_hash, _, _ = build_context(
                session,
                settings,
                request.task_id,
                request.mode,
                request.allowed_file_scopes,
                request.specialization,
                request.validation_commands,
            )
            if rechecked_hash != request.context_digest:
                raise PermissionError("Context changed during preparation")
        if cancel_requested(engine, identity):
            raise asyncio.CancelledError()
        from .models import TaskState

        with Session(engine) as session:
            task_state = session.get(Task, request.task_id).state
        task_policy = load_yaml(settings.approval_policy, ApprovalPolicy)
        if task_state in {"pending", "failed"}:
            transition(engine, request.task_id, TaskState.READY, "orchestrator", task_policy)
        transition(engine, request.task_id, TaskState.RUNNING, "orchestrator", task_policy)
        task_started = True
        prompt = assemble_prompt(request, context)
        (directory / "context-manifest.json").write_text(
            json.dumps(
                {
                    **{k: v for k, v in context.items() if k != "artifacts"},
                    "artifacts": [
                        {k: v for k, v in a.items() if k != "content"} for a in context["artifacts"]
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        if request.mode != ExecutionMode.VALIDATION_ONLY:
            invoke = (
                adapter.continue_execution if request.continuation_session_id else adapter.execute
            )
            arguments = (
                [request.continuation_session_id, request, prompt, directory]
                if request.continuation_session_id
                else [request, prompt, directory]
            )
            if policy.trace_metadata:
                from agents import trace

                with trace(
                    "AEO single-task execution",
                    trace_id="trace_" + identity.replace("-", ""),
                    group_id=request.correlation_id,
                    metadata={
                        "execution_id": identity,
                        "role": request.agent_role,
                        "task_id": request.task_id,
                        "transport": adapter.name,
                    },
                ):
                    outcome = await invoke(
                        *arguments,
                        cancel_check=lambda: cancel_requested(engine, identity),
                        started=lambda pid: record_started(engine, identity, pid),
                    )
            else:
                outcome = await invoke(
                    *arguments,
                    cancel_check=lambda: cancel_requested(engine, identity),
                    started=lambda pid: record_started(engine, identity, pid),
                )
            from .execution_sessions import extract_session

            session_id = extract_session(outcome.stdout)
            redactor = Redactor()
            (directory / "raw-output.jsonl").write_text(
                redactor.clean(outcome.stdout), encoding="utf-8"
            )
            (directory / "stderr.log").write_text(redactor.clean(outcome.stderr), encoding="utf-8")
            evidence += [str(directory / "raw-output.jsonl"), str(directory / "stderr.log")]
            if outcome.cancelled:
                result_state = E.CANCELLED
            elif outcome.timed_out:
                result_state = E.TIMED_OUT
            elif outcome.truncated:
                raise ValueError("Runtime output exceeded bounded log budget")
            elif outcome.exit_code:
                code = (
                    "authentication"
                    if any(
                        w in outcome.stderr.lower()
                        for w in ("unauthorized", "authentication", "401")
                    )
                    else "runtime-exit"
                )
                error = ExecutionError(code=code, message=redactor.clean(outcome.stderr[-1500:]))
            else:
                output, session_id, usage = parse_output(outcome.stdout)
                output = type(output).model_validate_json(redactor.clean(output.model_dump_json()))
                result_state = E.SUCCEEDED if not output.errors else E.FAILED
        else:
            record_started(engine, identity, os.getpid())
            result_state = E.SUCCEEDED
        if result_state == E.SUCCEEDED:
            for command in context["validation_commands"]:
                name = next(
                    (
                        p.split("=", 1)[1].strip('"')
                        for p in permissions
                        if p.startswith("default_permissions=")
                    ),
                    "",
                )
                argv = [
                    executable(settings),
                    *permissions,
                    "sandbox",
                    "--permission-profile",
                    name,
                    "--cd",
                    str(cwd),
                    "--",
                    *command["argv"],
                ]
                checked = await CodexProcessManager(policy.max_log_bytes).run(
                    argv,
                    cwd,
                    "",
                    command["timeout_seconds"],
                    cancel_check=lambda: cancel_requested(engine, identity),
                )
                validation.append(
                    {
                        "id": command["id"],
                        "argv": command["argv"],
                        "exit_code": checked.exit_code,
                        "timed_out": checked.timed_out,
                        "cancelled": checked.cancelled,
                        "stdout": Redactor().clean(checked.stdout),
                        "stderr": Redactor().clean(checked.stderr),
                    }
                )
                if checked.cancelled or checked.timed_out or checked.exit_code or checked.truncated:
                    result_state = (
                        E.CANCELLED
                        if checked.cancelled
                        else E.TIMED_OUT
                        if checked.timed_out
                        else E.FAILED
                    )
                    break
    except asyncio.CancelledError:
        result_state = E.CANCELLED
    except Exception as exc:
        error = ExecutionError(
            code="policy"
            if isinstance(exc, PermissionError)
            else "output-parse"
            if isinstance(exc, (ValueError, json.JSONDecodeError))
            else "execution-error",
            message=Redactor().clean(str(exc)),
        )
        result_state = E.FAILED
    finally:
        if cwd.exists() and before:
            try:
                after = tree_fingerprints(cwd, policy.max_artifact_bytes)
                from .execution_workspace import changed_files

                changes = changed_files(before, after)
                if request.mode == ExecutionMode.READ_ONLY and changes:
                    raise PermissionError("Read-only execution changed repository files")
                if request.mode != ExecutionMode.READ_ONLY:
                    changes, archive = preserve(cwd, directory, before, policy.max_artifact_bytes)
                    evidence.append(archive)
                    check_changes(changes, request.allowed_file_scopes)
            except Exception as exc:
                result_state = E.FAILED
                error = ExecutionError(code="artifact-policy", message=Redactor().clean(str(exc)))
    if result_state == E.SUCCEEDED:
        try:
            with Session(engine) as session:
                _, final_context_hash, _, _ = build_context(
                    session,
                    settings,
                    request.task_id,
                    request.mode,
                    request.allowed_file_scopes,
                    request.specialization,
                    request.validation_commands,
                )
                if final_context_hash != request.context_digest:
                    raise PermissionError("Approved context changed while the runtime was active")
        except Exception as exc:
            result_state = E.FAILED
            error = ExecutionError(code="context-invalidated", message=Redactor().clean(str(exc)))
    verified = (
        result_state == E.SUCCEEDED
        and bool(validation)
        and all(v["exit_code"] == 0 for v in validation)
    )
    result = ExecutionResult(
        execution_id=identity,
        task_id=request.task_id,
        agent_role=request.agent_role,
        session_id=session_id,
        status=result_state,
        started_at=started_at,
        ended_at=now(),
        duration_seconds=time.monotonic() - clock,
        summary=output.summary if output else (error.message if error else result_state.value),
        changed_files=changes,
        generated_artifacts=output.artifacts_created if output else [],
        logs=[p for p in evidence if p.endswith((".log", ".jsonl"))],
        exit_code=outcome.exit_code if outcome else None,
        error=error,
        usage=usage,
        validation_results=validation,
        implementation_verified=verified,
        evidence_references=evidence,
        output=output,
    )
    if (
        policy.input_price_per_million is not None
        and policy.output_price_per_million is not None
        and usage
    ):
        result.estimated_cost = (
            usage.get("input_tokens", 0) * policy.input_price_per_million
            + usage.get("output_tokens", 0) * policy.output_price_per_million
        ) / 1000000
    # Runtime success and task acceptance are separate. Unvalidated write tasks do not succeed.
    accepted = result_state == E.SUCCEEDED and (request.mode == ExecutionMode.READ_ONLY or verified)
    with Session(engine) as session, session.begin():
        execution = session.get(Execution, identity)
        if execution.state == E.PREPARING:
            # Startup failure has no running process; all terminal error states remain auditable.
            change(
                session,
                execution,
                E.CANCELLED if result_state == E.CANCELLED else E.FAILED,
                {"startup_failure": True},
            )
        else:
            change(session, execution, result_state, {"implementation_verified": verified})
        execution.result = result.model_dump(mode="json")
        execution.session_id = session_id
        if task_started:
            task = session.get(Task, request.task_id)
            task.state = (
                "succeeded"
                if accepted
                else "cancelled"
                if result_state == E.CANCELLED
                else "failed"
            )
            run = session.scalar(select(Run).where(Run.task_id == task.id, Run.status == "running"))
            if run:
                run.status, run.finished_at = task.state, now()
                audit(session, run.id, "run.finished", "orchestrator", {"status": run.status})
            audit(
                session,
                task.id,
                "task.transitioned",
                "orchestrator",
                {
                    "from": "running",
                    "to": task.state,
                    "execution_id": identity,
                    "orchestrator_validation_passed": verified,
                },
            )
    store_report(settings, identity, result)
    logging.getLogger(__name__).info(
        "execution_finished %s",
        json.dumps(
            {
                "execution_id": identity,
                "correlation_id": request.correlation_id,
                "project": request.project_id,
                "milestone": request.milestone_id,
                "task": request.task_id,
                "role": request.agent_role,
                "executor": adapter.name,
                "duration": result.duration_seconds,
                "retry_count": 0,
                "outcome": result.status,
                "usage": usage,
            }
        ),
    )
    return result


def execution_status(engine, identity: str) -> dict:
    with Session(engine) as session:
        execution = session.get(Execution, identity)
        if execution is None:
            raise ValueError("Unknown execution")
        return {
            "id": execution.id,
            "task_id": execution.task_id,
            "state": execution.state,
            "cancel_requested": execution.cancel_requested,
            "session_id": execution.session_id,
            "request": execution.request,
            "validation_commands": execution.context.get("validation_commands", []),
            "runtime_identity": execution.context.get("runtime_identity"),
            "execution_policy": execution.context.get("policy"),
            "context_digest": execution.request["context_digest"],
            "result": execution.result,
            "attempts": [
                {"state": a.state, "created_at": a.created_at, "payload": a.payload}
                for a in session.scalars(
                    select(ExecutionAttempt)
                    .where(ExecutionAttempt.execution_id == identity)
                    .order_by(ExecutionAttempt.created_at, ExecutionAttempt.id)
                )
            ],
        }
