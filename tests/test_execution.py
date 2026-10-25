import asyncio
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy.orm import Session
from test_design import ACTOR, HumanFixture, approve
from test_design import design_workspace as design_workspace
from typer.testing import CliRunner

from agrosphere_orchestrator.cli import app
from agrosphere_orchestrator.codex_runtime import doctor, parse_output
from agrosphere_orchestrator.config.settings import Settings
from agrosphere_orchestrator.execution import (
    approve_execution,
    cancel_execution,
    execution_status,
    queue_execution,
    run_execution,
)
from agrosphere_orchestrator.execution_models import AgentOutput, ExecutionMode
from agrosphere_orchestrator.execution_process import (
    CodexProcessManager,
    ProcessOutcome,
    Redactor,
    runtime_environment,
)
from agrosphere_orchestrator.execution_sessions import CodexSessionManager
from agrosphere_orchestrator.persistence import Execution, Task, import_plan
from agrosphere_orchestrator.state import record_approval

SESSION = "11111111-1111-4111-8111-111111111111"


def stream(output=None):
    output = output or AgentOutput(
        summary="Fixture proposal created",
        work_performed=["fixture"],
        files_changed=["src/generated.txt"],
        artifacts_created=[],
        commands_executed=["claimed test"],
        validation_evidence=["model assertion only"],
        errors=[],
        warnings=[],
        unresolved_issues=[],
        suggested_next_actions=[],
    )
    return "\n".join(
        json.dumps(e)
        for e in [
            {"type": "thread.started", "thread_id": SESSION},
            {
                "type": "item.completed",
                "item": {"type": "agent_message", "text": output.model_dump_json()},
            },
            {"type": "turn.completed", "usage": {"input_tokens": 10, "output_tokens": 5}},
        ]
    )


class TransportFixture:
    name = "fixture-no-live-codex"

    def __init__(self, kind="success"):
        self.kind = kind
        self.calls = 0

    async def execute(self, request, prompt, directory, **callbacks):
        self.calls += 1
        assert "untrusted task data" in prompt
        assert "Return exactly the AgentOutput" in prompt
        callbacks["started"](os.getpid())
        if self.kind == "startup":
            raise FileNotFoundError("fixture runtime startup failed")
        if request.mode == ExecutionMode.WORKTREE_WRITE:
            p = Path(request.worktree_path) / (
                "README.md" if self.kind == "scope" else "src/generated.txt"
            )
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("Fixture output only", encoding="utf-8")
        if self.kind == "auth":
            return ProcessOutcome(1, "", "401 authentication failed")
        if self.kind == "timeout":
            return ProcessOutcome(-1, stream(), "", timed_out=True)
        if self.kind == "cancel":
            return ProcessOutcome(-1, stream(), "", cancelled=True)
        return ProcessOutcome(0, "not JSON" if self.kind == "malformed" else stream(), "")

    async def continue_execution(self, session, request, prompt, directory, **callbacks):
        assert session == SESSION
        return await self.execute(request, prompt, directory, **callbacks)


@pytest.fixture
def execution_fixture(engine, design_workspace, policy, tmp_path, monkeypatch, request):
    f = design_workspace
    if getattr(request, "param", None) == "validation-task":
        f.inputs.plan.tasks[0].operation = "validate"
        f.inputs.plan.tasks[0].role = "qa-engineer"
    approve(engine, f)
    registry = json.loads(f.registry.read_text())
    for role in registry["roles"]:
        role["allowed_repositories"] = ["estate", "agrosphere-architecture", "agrosphere-contracts"]
    registry_path = tmp_path / "execution-roles.json"
    registry_path.write_text(json.dumps(registry))
    policy_path = tmp_path / "execution-policy.json"
    policy_path.write_text(
        json.dumps(
            {
                "live_enabled": True,
                "validation_commands": [
                    {
                        "id": "fixture-test",
                        "argv": [sys.executable, "-c", "print('fixture validation')"],
                    }
                ],
            }
        )
    )
    approvals = tmp_path / "task-approvals.json"
    approvals.write_text(policy.model_dump_json())
    settings = Settings(
        _env_file=None,
        repository_manifest=f.manifest,
        role_registry=registry_path,
        execution_policy=policy_path,
        execution_root=tmp_path / "private-executions",
        approval_policy=approvals,
        execution_approvers=[ACTOR],
    )
    task = import_plan(engine, f.inputs.plan)[0]
    record_approval(engine, task, f.inputs.plan.tasks[0].operation, "human", True, policy)
    monkeypatch.setattr(
        "agrosphere_orchestrator.execution.executable", lambda settings: "fixture-codex.exe"
    )
    monkeypatch.setattr(
        "agrosphere_orchestrator.execution_context.runtime_identity",
        lambda settings: {"path": "fixture-codex.exe", "version": "fixture", "sha256": "fixture"},
    )
    f.settings, f.task, f.policy_path = settings, task, policy_path
    return f


def queue(engine, f, commands=None):
    identity = queue_execution(
        engine, f.settings, f.task, mode="WORKTREE_WRITE", scopes=["src"], command_ids=commands
    )
    approve_execution(engine, f.settings, identity, HumanFixture())
    return identity


def invoke(engine, f, identity, transport):
    return asyncio.run(
        run_execution(
            engine,
            f.settings,
            identity,
            adapter=transport,
            isolation_probe=lambda *args: {"fixture": True, "not_live_isolation_proof": True},
        )
    )


def test_success_persists_session_but_model_claim_is_not_validation(engine, execution_fixture):
    f = execution_fixture
    original = (f.repos["estate"] / "README.md").read_bytes()
    identity = queue(engine, f)
    result = invoke(engine, f, identity, TransportFixture())
    assert result.status == "SUCCEEDED" and result.session_id == SESSION
    assert not result.implementation_verified
    assert result.changed_files == ["src/generated.txt"]
    assert (f.repos["estate"] / "README.md").read_bytes() == original
    assert not (f.repos["estate"] / "src/generated.txt").exists()
    with Session(engine) as session:
        assert session.get(Task, f.task).state == "failed"
    state = execution_status(engine, identity)
    assert state["state"] == "SUCCEEDED" and state["result"]["usage"]["input_tokens"] == 10
    assert (f.settings.execution_root / identity / "REPORT.md").exists()
    assert any(a["state"] == "RUNNING" for a in state["attempts"])


def test_orchestrator_allowlisted_validation_marks_task_accepted(
    engine, execution_fixture, monkeypatch
):
    f = execution_fixture

    class ValidationFixture:
        def __init__(self, *args):
            pass

        async def run(self, argv, cwd, prompt, timeout, **kwargs):
            assert "sandbox" in argv and sys.executable in argv
            return ProcessOutcome(0, "fixture validator passed", "")

    monkeypatch.setattr("agrosphere_orchestrator.execution.CodexProcessManager", ValidationFixture)
    identity = queue(engine, f, ["fixture-test"])
    result = invoke(engine, f, identity, TransportFixture())
    assert result.implementation_verified and result.validation_results[0]["exit_code"] == 0
    with Session(engine) as session:
        assert session.get(Task, f.task).state == "succeeded"


@pytest.mark.parametrize(
    "kind,expected,code",
    [
        ("startup", "FAILED", "execution-error"),
        ("auth", "FAILED", "authentication"),
        ("malformed", "FAILED", "output-parse"),
        ("timeout", "TIMED_OUT", None),
        ("cancel", "CANCELLED", None),
        ("scope", "FAILED", "artifact-policy"),
    ],
)
def test_error_timeout_cancel_and_scope_cases(engine, execution_fixture, kind, expected, code):
    f = execution_fixture
    identity = queue(engine, f)
    result = invoke(engine, f, identity, TransportFixture(kind))
    assert result.status == expected
    assert execution_status(engine, identity)["state"] == expected
    if code:
        assert result.error.code == code
    assert not result.implementation_verified
    assert (f.settings.execution_root / identity / "preserved-worktree.tar").exists()


def test_cannot_bypass_execution_grant_or_replay(engine, execution_fixture):
    f = execution_fixture
    identity = queue_execution(engine, f.settings, f.task, mode="WORKTREE_WRITE", scopes=["src"])
    adapter = TransportFixture()
    with pytest.raises(PermissionError, match="approval"):
        invoke(engine, f, identity, adapter)
    assert adapter.calls == 0
    with pytest.raises(PermissionError, match="approver"):
        approve_execution(engine, f.settings, identity, HumanFixture("agent-name"))
    approve_execution(engine, f.settings, identity, HumanFixture())
    invoke(engine, f, identity, adapter)
    with pytest.raises(PermissionError, match="unconsumed"):
        invoke(engine, f, identity, adapter)
    assert adapter.calls == 1


def test_context_change_invalidates_grant_before_model_start(engine, execution_fixture):
    f = execution_fixture
    identity = queue(engine, f)
    registry = json.loads(f.settings.role_registry.read_text())
    registry["roles"][4]["system_instructions"] += " changed approved instructions"
    f.settings.role_registry.write_text(json.dumps(registry))
    adapter = TransportFixture()
    with pytest.raises(PermissionError, match="Context"):
        invoke(engine, f, identity, adapter)
    assert adapter.calls == 0


def test_unauthorized_repo_and_protected_scope_blocked(engine, execution_fixture):
    f = execution_fixture
    for scope in [".", "../other", ".git", ".codex", "docs/milestones/FIXTURE-1"]:
        with pytest.raises((PermissionError, ValueError)):
            queue_execution(engine, f.settings, f.task, mode="WORKTREE_WRITE", scopes=[scope])
    registry = json.loads(f.settings.role_registry.read_text())
    registry["roles"][4]["allowed_repositories"] = ["unknown-repository"]
    f.settings.role_registry.write_text(json.dumps(registry))
    with pytest.raises(PermissionError, match="repository"):
        queue_execution(engine, f.settings, f.task, mode="WORKTREE_WRITE", scopes=["src"])


def test_cancel_pending_is_confirmed_without_process(engine, execution_fixture):
    f = execution_fixture
    identity = queue(engine, f)
    assert cancel_execution(engine, identity) == "CANCELLED"
    assert execution_status(engine, identity)["state"] == "CANCELLED"


def test_expired_approval_fails_closed(engine, execution_fixture):
    f = execution_fixture
    identity = queue(engine, f)
    # Grant records are immutable. Expiry is exercised with a controlled clock, not row mutation.
    from datetime import UTC, datetime, timedelta

    import agrosphere_orchestrator.execution as service

    class FutureClock:
        @staticmethod
        def now(tz):
            return datetime.now(UTC) + timedelta(days=1)

        fromisoformat = datetime.fromisoformat

    original = service.datetime
    service.datetime = FutureClock
    try:
        with pytest.raises(PermissionError, match="expired"):
            invoke(engine, f, identity, TransportFixture())
    finally:
        service.datetime = original


def test_recovery_marks_orphan_interrupted_without_success_or_replay(
    engine, execution_fixture, monkeypatch
):
    from agrosphere_orchestrator.execution import change

    f = execution_fixture
    identity = queue(engine, f)
    with Session(engine) as session, session.begin():
        change(
            session,
            session.get(Execution, identity),
            "PREPARING",
            {"owner_pid": 123, "owner_identity": "old"},
        )
    monkeypatch.setattr(
        "agrosphere_orchestrator.execution_sessions.process_identity", lambda pid: None
    )
    assert CodexSessionManager(engine).reconcile()[0]["state"] == "INTERRUPTED"
    assert execution_status(engine, identity)["result"] is None
    recovery = queue_execution(
        engine,
        f.settings,
        f.task,
        mode="WORKTREE_WRITE",
        scopes=["src"],
        parent=identity,
        instructions="Review the preserved partial fixture, then propose bounded recovery",
    )
    assert execution_status(engine, recovery)["request"]["parent_execution_id"] == identity
    assert execution_status(engine, recovery)["request"]["approval_reference"] is None


def test_worktree_creation_failure_preserves_original(engine, execution_fixture, monkeypatch):
    f = execution_fixture
    identity = queue(engine, f)

    def fail(*args):
        raise RuntimeError("fixture worktree creation failed")

    monkeypatch.setattr("agrosphere_orchestrator.execution.create_worktree", fail)
    result = invoke(engine, f, identity, TransportFixture())
    assert result.status == "FAILED" and "worktree" in result.error.message
    assert (f.repos["estate"] / "README.md").read_text() == "Verified fixture context only.\n"


def test_real_process_timeout_and_cancel_are_confirmed(tmp_path):
    manager = CodexProcessManager()
    script = "import sys,time; sys.stdin.read(); print('started',flush=True); time.sleep(10)"
    outcome = asyncio.run(manager.run([sys.executable, "-c", script], tmp_path, "fixture", 0.2))
    assert outcome.timed_out and outcome.exit_code is not None
    outcome = asyncio.run(
        manager.run(
            [sys.executable, "-c", script], tmp_path, "fixture", 10, cancel_check=lambda: True
        )
    )
    assert outcome.cancelled and outcome.exit_code is not None


def test_result_parser_and_secret_redaction(monkeypatch):
    output, session, usage = parse_output(stream())
    assert output.summary and session == SESSION and usage["output_tokens"] == 5
    for raw in ("not-json", json.dumps({"type": "turn.completed"}), json.dumps({"type": "error"})):
        with pytest.raises((ValueError, RuntimeError)):
            parse_output(raw)
    monkeypatch.setenv("PRODUCTION_PASSWORD", "fixture-secret-value")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "fixture-aws-value")
    assert "fixture-secret-value" not in Redactor().clean("password=fixture-secret-value")
    assert (
        "PRODUCTION_PASSWORD" not in runtime_environment()
        and "AWS_ACCESS_KEY_ID" not in runtime_environment()
    )


def test_doctor_detects_mcp_absence_without_model(monkeypatch):
    def probe(argv, **kwargs):
        if "--version" in argv:
            return SimpleNamespace(returncode=0, stdout="codex-cli fixture", stderr="")
        if "mcp-server" in argv:
            return SimpleNamespace(returncode=2, stdout="", stderr="unsupported")
        if "login" in argv:
            return SimpleNamespace(returncode=0, stdout="Logged in using ChatGPT", stderr="")
        return SimpleNamespace(
            returncode=0,
            stdout="--json --output-schema --ignore-user-config --ignore-rules",
            stderr="",
        )

    monkeypatch.setattr(
        "agrosphere_orchestrator.codex_runtime.executable", lambda s: "fixture-codex.exe"
    )
    monkeypatch.setattr("agrosphere_orchestrator.codex_runtime.subprocess.run", probe)
    result = doctor(Settings())
    assert result.exec_supported and result.authenticated and not result.mcp_supported
    assert result.selected_transport == "exec"


def test_cli_roles_and_execution_status(engine, execution_fixture, monkeypatch):
    f = execution_fixture
    monkeypatch.setenv("AEO_ROLE_REGISTRY", str(f.settings.role_registry))
    runner = CliRunner()
    roles = runner.invoke(app, ["agents", "list"])
    assert roles.exit_code == 0 and len(json.loads(roles.stdout)) == 9
    detail = runner.invoke(app, ["agents", "describe", "developer"])
    assert detail.exit_code == 0 and "data-postgis" in detail.stdout
    identity = queue(engine, f)
    state = runner.invoke(app, ["agent", "status", "--execution", identity])
    assert state.exit_code == 0 and json.loads(state.stdout)["state"] == "AWAITING_APPROVAL"
    result = runner.invoke(app, ["agent", "cancel", "--execution", identity])
    assert result.exit_code == 0 and json.loads(result.stdout)["cancellation_confirmed"]


def test_native_isolation_failure_blocks_model_invocation(engine, execution_fixture):
    f = execution_fixture
    identity = queue(engine, f)
    adapter = TransportFixture()

    def denied(*args):
        raise PermissionError("fixture isolation unavailable")

    result = asyncio.run(
        run_execution(engine, f.settings, identity, adapter=adapter, isolation_probe=denied)
    )
    assert result.status == "FAILED" and adapter.calls == 0
    assert "isolation unavailable" in result.error.message


def test_policy_disabled_never_calls_runtime(engine, execution_fixture):
    f = execution_fixture
    policy = json.loads(f.policy_path.read_text())
    policy["live_enabled"] = False
    f.policy_path.write_text(json.dumps(policy))
    identity = queue(engine, f)
    adapter = TransportFixture()
    with pytest.raises(PermissionError, match="disabled"):
        invoke(engine, f, identity, adapter)
    assert adapter.calls == 0


def test_validation_failure_is_not_accepted(engine, execution_fixture, monkeypatch):
    f = execution_fixture

    class FailedValidator:
        def __init__(self, *args):
            pass

        async def run(self, *args, **kwargs):
            return ProcessOutcome(1, "fixture tests failed", "")

    monkeypatch.setattr("agrosphere_orchestrator.execution.CodexProcessManager", FailedValidator)
    identity = queue(engine, f, ["fixture-test"])
    result = invoke(engine, f, identity, TransportFixture())
    assert result.status == "FAILED" and not result.implementation_verified
    with Session(engine) as session:
        assert session.get(Task, f.task).state == "failed"


@pytest.mark.parametrize("execution_fixture", ["validation-task"], indirect=True)
def test_validation_only_runs_no_model(engine, execution_fixture, monkeypatch):
    f = execution_fixture

    class Validator:
        def __init__(self, *args):
            pass

        async def run(self, *args, **kwargs):
            return ProcessOutcome(0, "fixture tests passed", "")

    monkeypatch.setattr("agrosphere_orchestrator.execution.CodexProcessManager", Validator)
    identity = queue_execution(
        engine,
        f.settings,
        f.task,
        mode="VALIDATION_ONLY",
        scopes=["src"],
        command_ids=["fixture-test"],
    )
    approve_execution(engine, f.settings, identity, HumanFixture())
    adapter = TransportFixture()
    result = invoke(engine, f, identity, adapter)
    assert result.implementation_verified and adapter.calls == 0


def test_cleanup_requires_unchanged_preservation_and_keeps_source(engine, execution_fixture):
    from agrosphere_orchestrator.execution_workspace import cleanup_worktree

    f = execution_fixture
    identity = queue(engine, f)
    invoke(engine, f, identity, TransportFixture())
    directory = f.settings.execution_root / identity
    workspace = directory / "worktree"
    original = (f.repos["estate"] / "README.md").read_bytes()
    (workspace / "src/generated.txt").write_text("changed after preservation")
    with pytest.raises(PermissionError, match="changed"):
        cleanup_worktree(f.repos["estate"], workspace, f.settings.execution_root, directory)
    assert (f.repos["estate"] / "README.md").read_bytes() == original
    with pytest.raises(PermissionError, match="outside"):
        cleanup_worktree(f.repos["estate"], f.repos["estate"], f.settings.execution_root, directory)


def test_execution_grants_and_attempts_are_append_only(engine, execution_fixture):
    from sqlalchemy import text
    from sqlalchemy.exc import IntegrityError

    f = execution_fixture
    identity = queue(engine, f)
    for table in ("execution_grants", "execution_attempts"):
        with pytest.raises(IntegrityError, match="append-only"):
            with engine.begin() as connection:
                connection.execute(text(f"DELETE FROM {table}"))
    assert execution_status(engine, identity)["state"] == "AWAITING_APPROVAL"


def test_mcp_incompatibility_does_not_fall_back_to_unrestricted_tools(monkeypatch):
    from agrosphere_orchestrator.codex_runtime import CodexMCPAdapter

    adapter = CodexMCPAdapter(Settings())

    async def incompatible():
        return SimpleNamespace(mcp_supported=False)

    monkeypatch.setattr(adapter, "health_check", incompatible)
    with pytest.raises(RuntimeError, match="mcp-server"):
        asyncio.run(adapter.tools())


def test_unallowlisted_validation_and_unknown_specialization_rejected(engine, execution_fixture):
    f = execution_fixture
    with pytest.raises(PermissionError, match="allowlist"):
        queue_execution(
            engine,
            f.settings,
            f.task,
            mode="WORKTREE_WRITE",
            scopes=["src"],
            command_ids=["arbitrary-shell"],
        )
    with pytest.raises(PermissionError, match="specialization"):
        queue_execution(
            engine,
            f.settings,
            f.task,
            mode="WORKTREE_WRITE",
            scopes=["src"],
            specialization="unrestricted-admin",
        )


def test_normal_smoke_entrypoint_is_offline():
    import subprocess

    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "scripts/codex_live_smoke.py"],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0 and "SKIPPED" in result.stdout


def test_worktree_checkout_does_not_execute_repository_hooks(engine, execution_fixture):
    f = execution_fixture
    marker = f.settings.execution_root.parent / "unexpected-hook.txt"
    hook = f.repos["estate"] / ".git/hooks/post-checkout"
    hook.write_text('#!/bin/sh\necho invoked > "' + marker.as_posix() + '"\n', encoding="utf-8")
    hook.chmod(0o755)
    identity = queue(engine, f)
    result = invoke(engine, f, identity, TransportFixture())
    assert result.status == "SUCCEEDED" and not marker.exists()


def test_global_active_slot_is_atomic(engine, execution_fixture):
    from uuid import uuid4

    from sqlalchemy.exc import IntegrityError

    from agrosphere_orchestrator.execution import change
    from agrosphere_orchestrator.persistence import Execution

    f = execution_fixture
    identity = queue(engine, f)
    with Session(engine) as session, session.begin():
        first = session.get(Execution, identity)
        request_data, context_data = first.request, first.context
        change(session, first, "PREPARING")
    with pytest.raises(IntegrityError):
        with Session(engine) as session, session.begin():
            second = Execution(
                id=str(uuid4()),
                task_id=f.task,
                state="AWAITING_APPROVAL",
                request=request_data,
                context=context_data,
                cancel_requested=False,
            )
            session.add(second)
            session.flush()
            change(session, second, "PREPARING")


def test_unknown_process_identity_blocks_recovery(engine, execution_fixture, monkeypatch):
    from agrosphere_orchestrator.execution import change

    f = execution_fixture
    identity = queue(engine, f)
    with Session(engine) as session, session.begin():
        change(
            session,
            session.get(Execution, identity),
            "PREPARING",
            {"owner_pid": 123, "owner_identity": "unverifiable"},
        )
    monkeypatch.setattr(
        "agrosphere_orchestrator.execution_sessions.process_identity", lambda pid: "UNKNOWN"
    )
    findings = CodexSessionManager(engine).reconcile()
    assert findings[0]["state"] == "PREPARING"
    assert "blocked" in findings[0]["finding"]


def test_configuration_rejects_duplicate_validators():
    from agrosphere_orchestrator.execution_models import ExecutionPolicy

    with pytest.raises(ValueError, match="Duplicate"):
        ExecutionPolicy(
            validation_commands=[{"id": "same", "argv": ["one"]}, {"id": "same", "argv": ["two"]}]
        )


def test_redaction_preserves_normal_risk_and_disk_language():
    text = "risk-based-analysis and disk-full-read-access; token=sk-example_secret_key_123456"
    cleaned = Redactor().clean(text)
    assert "risk-based-analysis" in cleaned and "disk-full-read-access" in cleaned
    assert "sk-example_secret_key_123456" not in cleaned


def test_expired_grant_prevents_followup_validation_action(engine, execution_fixture, monkeypatch):
    from datetime import UTC, datetime, timedelta

    import agrosphere_orchestrator.execution as service

    f = execution_fixture

    class FutureClock:
        @staticmethod
        def now(tz):
            return datetime.now(UTC) + timedelta(days=1)

        fromisoformat = datetime.fromisoformat

    class ExpiringTransport(TransportFixture):
        async def execute(self, *args, **kwargs):
            outcome = await super().execute(*args, **kwargs)
            monkeypatch.setattr(service, "datetime", FutureClock)
            return outcome

    class ForbiddenValidator:
        def __init__(self, *args):
            raise AssertionError("expired grant must not reach validator startup")

    monkeypatch.setattr(service, "CodexProcessManager", ForbiddenValidator)
    identity = queue(engine, f, ["fixture-test"])
    result = invoke(engine, f, identity, ExpiringTransport())
    assert result.status == "FAILED" and result.error.code == "policy"
    assert "expired" in result.error.message
