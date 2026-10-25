"""All orchestration tests use temporary repositories and deterministic mock transports."""

import asyncio
import hashlib
import json
import sys

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from test_design import ACTOR, HumanFixture, approve
from test_design import design_workspace as design_workspace
from test_execution import TransportFixture

from agrosphere_orchestrator.config.settings import Settings
from agrosphere_orchestrator.execution import approve_execution
from agrosphere_orchestrator.execution_models import ExecutionMode
from agrosphere_orchestrator.execution_process import ProcessOutcome
from agrosphere_orchestrator.models import MilestoneSpec, TaskSpec
from agrosphere_orchestrator.orchestration import (
    TaskScheduler,
    approve_plan,
    milestone_report,
    propose_plan,
    publish_handoff,
)
from agrosphere_orchestrator.orchestration_models import (
    ArtifactReference,
    ExecutionPlan,
    TaskOptions,
)
from agrosphere_orchestrator.orchestration_store import (
    OrchestrationEvidence,
    ResourceLease,
    TaskClaim,
    acquire,
    evidence,
    transaction,
)
from agrosphere_orchestrator.persistence import Execution, Milestone, Task, import_plan
from agrosphere_orchestrator.state import record_approval


@pytest.fixture
def orchestration_fixture(engine, design_workspace, policy, tmp_path, monkeypatch):
    f = design_workspace
    specs = []
    workflow = [
        ("program", "program-manager", "estate", []),
        ("planning", "project-manager", "estate", ["program"]),
        ("requirements", "business-analyst", "estate", ["planning"]),
        ("architecture", "solution-architect", "estate", ["requirements"]),
        ("dev-a", "developer", "estate", ["architecture"]),
        ("dev-b", "developer", "agrosphere-architecture", ["architecture"]),
        ("qa", "qa-engineer", "estate", ["dev-a", "dev-b"]),
        ("security", "security-engineer", "agrosphere-architecture", ["dev-a", "dev-b"]),
        ("devops", "devops-engineer", "estate", ["qa", "security"]),
        ("docs", "technical-writer", "estate", ["devops"]),
    ]
    for identity, role, repository, deps in workflow:
        specs.append(
            TaskSpec(
                id=identity,
                title="Fixture " + identity,
                role=role,
                repository=repository,
                operation="code-write" if identity.startswith("dev-") else "inspect",
                depends_on=deps,
                acceptance_criteria=["fixture evidence accepted"],
            )
        )
    f.inputs.plan.tasks = specs
    approve(engine, f)
    registry = json.loads(f.registry.read_text())
    for role in registry["roles"]:
        role["allowed_repositories"] = list(f.repos)
    registry_path = tmp_path / "roles.json"
    registry_path.write_text(json.dumps(registry))
    execution_policy = tmp_path / "execution.json"
    execution_policy.write_text(
        json.dumps(
            {
                "live_enabled": True,
                "validation_commands": [
                    {
                        "id": "fixture-check",
                        "argv": [sys.executable, "-c", "print('fixture validated')"],
                    }
                ],
            }
        )
    )
    approvals = tmp_path / "approvals.json"
    approvals.write_text(policy.model_dump_json())
    f.settings = Settings(
        _env_file=None,
        repository_manifest=f.manifest,
        role_registry=registry_path,
        execution_policy=execution_policy,
        execution_root=tmp_path / "private",
        approval_policy=approvals,
        execution_approvers=[ACTOR],
    )
    for task in import_plan(engine, f.inputs.plan):
        with Session(engine) as session:
            operation = session.get(Task, task).spec["operation"]
        record_approval(engine, task, operation, "human", True, policy)
    monkeypatch.setattr(
        "agrosphere_orchestrator.execution.executable", lambda _: "fixture-codex.exe"
    )
    monkeypatch.setattr(
        "agrosphere_orchestrator.execution_context.runtime_identity",
        lambda _: {"path": "fixture", "version": "fixture", "sha256": "fixture"},
    )

    class Validator:
        def __init__(self, *args):
            pass

        async def run(self, *args, **kwargs):
            return ProcessOutcome(0, "fixture checked", "")

    monkeypatch.setattr("agrosphere_orchestrator.execution.CodexProcessManager", Validator)
    f.options = {
        t.id: TaskOptions(
            mode=ExecutionMode.WORKTREE_WRITE,
            allowed_paths=["src"],
            expected_outputs=["src/generated.txt"],
            validation_commands=["fixture-check"],
        )
        if t.id.startswith("dev-")
        else TaskOptions()
        for t in specs
    }
    f.options["qa"].inputs = [
        ArtifactReference(
            repository="estate",
            path="src/generated.txt",
            sha256=hashlib.sha256(b"Fixture output only").hexdigest(),
            revision=next(c.head for c in f.inputs.context if c.repository == "estate"),
            producer="dev-a",
        )
    ]
    f.plan_id = propose_plan(engine, f.settings, "FIXTURE-1", f.options, "fixture")
    approve_plan(engine, f.settings, "FIXTURE-1", HumanFixture(), "fixture")
    return f


def scheduler(engine, f, transport=None):
    return TaskScheduler(
        engine,
        f.settings,
        adapter=transport or TransportFixture(),
        isolation_probe=lambda *args: {"fixture": True},
    )


async def granted_batch(engine, f, service):
    ids = await service.prepare("FIXTURE-1", "fixture")
    for identity in ids:
        approve_execution(engine, f.settings, identity, HumanFixture())
    return await service.execute_ready_tasks("FIXTURE-1", "fixture")


def test_full_multi_agent_fixture_and_concurrent_writes(engine, orchestration_fixture):
    f = orchestration_fixture

    class ConcurrentTransport(TransportFixture):
        active = 0
        peak = 0

        async def execute(self, request, *args, **kwargs):
            self.active += 1
            self.peak = max(self.peak, self.active)
            await asyncio.sleep(0.03)
            try:
                return await super().execute(request, *args, **kwargs)
            finally:
                self.active -= 1

    adapter = ConcurrentTransport()
    service = scheduler(engine, f, adapter)

    async def workflow():
        for _ in range(12):
            batch = await granted_batch(engine, f, service)
            if not batch["results"]:
                break

    asyncio.run(workflow())
    report = milestone_report(engine, "FIXTURE-1", "fixture")
    assert report["status"] == "COMPLETED", report
    assert any(e["kind"] == "handoff.published" for e in report["events"])
    assert any(e["kind"] == "handoff.acknowledged" for e in report["events"])
    assert adapter.peak == 2
    assert len(report["tasks"]) == 10
    assert len(report["parallel_batches"]) == 2
    assert not (f.repos["estate"] / "src/generated.txt").exists()
    with Session(engine) as session:
        assert not list(session.scalars(select(ResourceLease)))
        assert not list(session.scalars(select(TaskClaim)))


def test_plan_idempotence_and_invalid_graphs(engine, orchestration_fixture):
    f = orchestration_fixture
    assert propose_plan(engine, f.settings, "FIXTURE-1", f.options, "fixture") == f.plan_id
    for tasks in [
        [{"id": "one", "depends_on": ["missing"]}],
        [{"id": "one", "depends_on": ["two"]}, {"id": "two", "depends_on": ["one"]}],
        [{"id": "one"}, {"id": "one"}],
    ]:
        with pytest.raises(ValueError):
            MilestoneSpec(
                id="bad",
                project="fixture",
                title="bad",
                tasks=[
                    dict(
                        title="x",
                        repository="estate",
                        role="developer",
                        acceptance_criteria=["x"],
                        **t,
                    )
                    for t in tasks
                ],
            )
    with Session(engine) as session:
        from agrosphere_orchestrator.orchestration_store import PlanRevision

        plan = ExecutionPlan.model_validate(session.get(PlanRevision, f.plan_id).payload)
        assert "@startuml" in plan.plantuml() and "-->" in plan.plantuml()
    with pytest.raises(ValueError):
        TaskOptions(mode="WORKTREE_WRITE", allowed_paths=["../escape"])


def test_conflicting_writes_and_expired_leases_cannot_be_stolen(engine, orchestration_fixture):
    f = orchestration_fixture
    with transaction(engine) as session:
        tasks = list(session.scalars(select(Task)))
        assert acquire(session, tasks[0].id, "first", ["repository:estate"], True, -1)
        session.flush()
        assert not acquire(session, tasks[1].id, "second", ["repository:estate"], True, 100)
        assert not acquire(session, tasks[1].id, "second", ["repository:estate"], False, 100)
    service = scheduler(engine, f)
    batch = asyncio.run(granted_batch(engine, f, service))
    assert not batch["results"]
    assert any("resource conflict" in v for v in batch["blocked"].values())


def test_parallel_read_leases_safe_and_shared_resource_conflicts(engine, orchestration_fixture):
    with transaction(engine) as session:
        tasks = list(session.scalars(select(Task)))
        assert acquire(session, tasks[0].id, "a", ["repository:estate"], False, 100)
        session.flush()
        assert acquire(session, tasks[1].id, "b", ["repository:estate"], False, 100)
        assert acquire(session, tasks[0].id, "c", ["shared:contracts"], True, 100)
        session.flush()
        assert not acquire(session, tasks[1].id, "d", ["shared:contracts"], True, 100)


def test_bounded_retry_and_failed_dependency(engine, orchestration_fixture):
    f = orchestration_fixture
    transport = TransportFixture("auth")
    service = scheduler(engine, f, transport)
    asyncio.run(granted_batch(engine, f, service))
    batch = asyncio.run(service.schedule("FIXTURE-1", "fixture"))
    assert not batch["ready"] and "planning" in batch["blocked"]
    assert transport.calls == 1  # authentication is never retried


def test_transient_read_failure_stops_at_three_repairs(engine, orchestration_fixture):
    f = orchestration_fixture
    transport = TransportFixture("startup")
    service = scheduler(engine, f, transport)

    async def workflow():
        for _ in range(7):
            await granted_batch(engine, f, service)

    asyncio.run(workflow())
    assert transport.calls == 4  # original + three bounded repairs, each new exact grant
    assert milestone_report(engine, "FIXTURE-1", "fixture")["status"] == "INCOMPLETE"


def test_unapproved_or_modified_design_blocks_before_transport(engine, orchestration_fixture):
    f = orchestration_fixture
    service = scheduler(engine, f)
    from agrosphere_orchestrator.persistence import DesignCase, DesignRevision

    with Session(engine) as session:
        case = session.get(DesignCase, f.key)
        revision = session.get(DesignRevision, case.revision_id)
        artifact = revision.payload["artifacts"][0]
    # Use exported artifact metadata; no business repository is touched.
    from agrosphere_orchestrator.design import artifacts_of

    target = artifacts_of(revision)[0]
    (f.repos[target.repository] / target.path).write_text("invalidated")
    with pytest.raises(PermissionError, match="changed"):
        asyncio.run(service.schedule("FIXTURE-1", "fixture"))
    assert artifact


def test_missing_plan_approval_and_no_implicit_execution_approval(engine, orchestration_fixture):
    f = orchestration_fixture
    f.options["program"].priority = 1
    propose_plan(engine, f.settings, "FIXTURE-1", f.options, "fixture")
    service = scheduler(engine, f)
    with pytest.raises(PermissionError, match="human approval"):
        asyncio.run(service.prepare("FIXTURE-1", "fixture"))
    approve_plan(engine, f.settings, "FIXTURE-1", HumanFixture(), "fixture")
    asyncio.run(service.prepare("FIXTURE-1", "fixture"))
    assert not asyncio.run(service.execute_ready_tasks("FIXTURE-1", "fixture"))["results"]


def test_uncertain_interruption_retains_write_lock_and_blocks_resume(engine, orchestration_fixture):
    f = orchestration_fixture
    with transaction(engine) as session:
        task = session.scalar(select(Task).where(Task.external_id == "dev-a"))
        session.add(
            TaskClaim(
                task_id=task.id,
                owner="crashed",
                execution_id=None,
                expires_at="2000-01-01",
                reconciliation_required=False,
            )
        )
        assert acquire(session, task.id, "crashed", ["repository:estate"], True, -1)
    service = scheduler(engine, f)
    result = service.reconcile("FIXTURE-1", "fixture")
    assert result[0]["state"] == "reconciliation_required"
    with pytest.raises(PermissionError, match="reconciliation"):
        asyncio.run(service.resume("FIXTURE-1", "fixture"))
    with Session(engine) as session:
        assert list(session.scalars(select(ResourceLease)))


def test_pause_cancels_pending_assignment(engine, orchestration_fixture):
    f = orchestration_fixture
    service = scheduler(engine, f)
    asyncio.run(service.pause("FIXTURE-1", "fixture"))
    assert not asyncio.run(service.schedule("FIXTURE-1", "fixture"))["ready"]
    asyncio.run(service.resume("FIXTURE-1", "fixture"))
    assert asyncio.run(service.schedule("FIXTURE-1", "fixture"))["ready"]


def test_handoff_preserves_hash_revision_and_prompt_context(engine, orchestration_fixture):
    f = orchestration_fixture
    # A read-only report artifact already exists at a pinned committed source revision.
    data = (f.repos["estate"] / "README.md").read_bytes()
    ref = ArtifactReference(
        repository="estate",
        path="README.md",
        sha256=hashlib.sha256(data).hexdigest(),
        revision=f.inputs.context[-1].head,
    )
    f.options["planning"].inputs = [ref]
    propose_plan(engine, f.settings, "FIXTURE-1", f.options, "fixture")
    approve_plan(engine, f.settings, "FIXTURE-1", HumanFixture(), "fixture")
    service = scheduler(engine, f)
    asyncio.run(granted_batch(engine, f, service))
    ids = asyncio.run(service.prepare("FIXTURE-1", "fixture"))
    with Session(engine) as session:
        request = session.get(Execution, ids[0]).request
        assert any(
            a["sha256"] == ref.sha256 and a["revision"] == ref.revision
            for a in request["required_input_artifacts"]
        )
    (f.repos["estate"] / "README.md").write_text("corrupted")
    with pytest.raises(PermissionError):
        asyncio.run(service.prepare("FIXTURE-1", "fixture"))


def test_invalid_handoff_and_append_only_evidence(engine, orchestration_fixture):
    f = orchestration_fixture
    with pytest.raises(PermissionError, match="completed"):
        publish_handoff(engine, f.settings, "FIXTURE-1", "program", "planning", [], "x", "fixture")
    with transaction(engine) as session:
        milestone = session.scalar(select(Milestone))
        first = evidence(session, milestone.id, None, "test", {"x": 1}, "same-event")
        assert evidence(session, milestone.id, None, "test", {"x": 1}, "same-event") == first
    with engine.begin() as connection, pytest.raises(IntegrityError):
        connection.execute(text("DELETE FROM orchestration_evidence"))
    with Session(engine) as session:
        assert list(session.scalars(select(OrchestrationEvidence)))


def test_active_cancellation_is_confirmed_and_releases_claim(engine, orchestration_fixture):
    f = orchestration_fixture
    entered = asyncio.Event()

    class BlockingTransport(TransportFixture):
        async def execute(self, request, prompt, directory, **callbacks):
            entered.set()
            for _ in range(100):
                if callbacks["cancel_check"]():
                    return ProcessOutcome(-1, "", "", cancelled=True)
                await asyncio.sleep(0.01)
            raise AssertionError("Pause failed to cancel the active fixture")

    service = scheduler(engine, f, BlockingTransport())

    async def workflow():
        ids = await service.prepare("FIXTURE-1", "fixture")
        for identity in ids:
            approve_execution(engine, f.settings, identity, HumanFixture())
        batch = asyncio.create_task(service.execute_ready_tasks("FIXTURE-1", "fixture"))
        await entered.wait()
        await service.pause("FIXTURE-1", "fixture")
        return await batch

    result = asyncio.run(workflow())
    assert not result["results"][0]["accepted"]
    with Session(engine) as session:
        assert not list(session.scalars(select(TaskClaim)))
        assert not list(session.scalars(select(ResourceLease)))


def test_missing_architecture_approval_fails_closed(engine, orchestration_fixture):
    from agrosphere_orchestrator.persistence import DesignCase

    f = orchestration_fixture
    with Session(engine) as session, session.begin():
        session.get(DesignCase, f.key).state = "AWAITING_DESIGN_APPROVAL"
    with pytest.raises(PermissionError, match="approved design"):
        asyncio.run(scheduler(engine, f).prepare("FIXTURE-1", "fixture"))


def test_reconcile_confirmed_result_without_duplicate_execution(engine, orchestration_fixture):
    f = orchestration_fixture
    service = scheduler(engine, f)
    batch = asyncio.run(granted_batch(engine, f, service))
    result = batch["results"][0]
    with transaction(engine) as session:
        session.add(
            TaskClaim(
                task_id=result["task_id"],
                execution_id=result["execution_id"],
                owner="crash-after-result",
                expires_at="2000-01-01",
                reconciliation_required=False,
            )
        )
        acquire(session, result["task_id"], "crash-after-result", ["repository:estate"], False, -1)
    recovered = service.reconcile("FIXTURE-1", "fixture")
    assert recovered[0]["state"] == "succeeded"
    with Session(engine) as session:
        assert not list(session.scalars(select(TaskClaim)))
        assert len(list(session.scalars(select(Execution)))) == 1


def test_scheduler_cli_exposes_plan_and_reports(engine, orchestration_fixture):
    from typer.testing import CliRunner

    from agrosphere_orchestrator.cli import app

    f = orchestration_fixture
    runner = CliRunner()
    result = runner.invoke(
        app, ["milestone", "graph", "FIXTURE-1", "--project", "fixture", "--plantuml"]
    )
    assert result.exit_code == 0, result.output
    assert "@startuml" in result.output
    result = runner.invoke(app, ["milestone", "report", "FIXTURE-1", "--project", "fixture"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["plan_id"] == f.plan_id
    assert runner.invoke(app, ["agents", "workload"]).exit_code == 0
