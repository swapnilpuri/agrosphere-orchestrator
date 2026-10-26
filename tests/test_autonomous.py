"""Controller invariants on disposable DBs; no model/provider execution."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest
from pydantic import ValidationError
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from agrosphere_orchestrator.autonomous import AutonomousMilestoneController
from agrosphere_orchestrator.autonomous_models import (
    AutonomousRequest,
    BudgetExceeded,
    Roadmap,
    RunLimits,
    StepResult,
)
from agrosphere_orchestrator.autonomous_store import (
    AutonomousOperation,
    AutonomousRun,
    report,
)
from agrosphere_orchestrator.config.settings import Settings
from agrosphere_orchestrator.orchestration_store import transaction
from agrosphere_orchestrator.persistence import AuditEvent


class Ports:
    def __init__(self):
        self.calls = 0
        self.approved = False
        self.recovered = None

    def discover(self, request):
        return {"fixture": True}

    async def perform(self, step, request, value, guard):
        self.calls += 1
        if step == "RECONCILING":
            return StepResult(next_step="PREPARING_DESIGN", evidence={"fixture": "discovered"})
        return StepResult(
            next_step="PREPARING_DESIGN",
            checkpoint={"category": "design", "reason": "Fixture review"}
            if not self.approved
            else None,
        )

    async def recover(self, step, request, value):
        return self.recovered


@pytest.fixture
def controller(engine):
    return AutonomousMilestoneController(engine, Settings(_env_file=None), Ports())


def start(controller, **limits):
    value = controller.start(
        AutonomousRequest(milestone="AEO-TEST", mode="local", limits=RunLimits(**limits))
    )
    return value["run_id"]


def position(engine, identity, step="EXECUTING"):
    with transaction(engine) as session:
        run = session.get(AutonomousRun, identity)
        run.step, run.state = step, step
        operation = AutonomousOperation(
            id="fixture-operation",
            run_id=identity,
            sequence=1,
            step=step,
            request_hash=run.request_hash,
        )
        session.add(operation)
        session.flush()
        run.current_operation = operation.id
        run.usage = {**run.usage, "steps": 1}


def test_dry_run_has_no_state_or_audit_writes(engine, controller):
    with Session(engine) as session:
        count = session.scalar(select(func.count()).select_from(AuditEvent))
    result = controller.start(AutonomousRequest(milestone="AEO-TEST"))
    assert result["mutations"] is False
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(AutonomousRun)) == 0
        assert session.scalar(select(func.count()).select_from(AuditEvent)) == count


def test_checkpoint_resume_rechecks_approval_without_resetting_counters(engine, controller):
    identity = start(controller)
    value = asyncio.run(controller.run(identity))
    assert value["state"] == "AWAITING_APPROVAL"
    assert value["usage"]["steps"] == 2
    other = AutonomousMilestoneController(engine, controller.settings, controller.services)
    again = asyncio.run(other.resume(identity))
    assert again["state"] == "AWAITING_APPROVAL"
    assert again["usage"]["steps"] == 3
    assert again["formally_completed"] is False
    assert controller.validate(identity)["valid"]


def test_duplicate_run_cannot_reset_budget_or_change_scope(engine, controller):
    request = AutonomousRequest(milestone="AEO-TEST", mode="local")
    identity = controller.start(request, "fixed")["run_id"]
    asyncio.run(controller.run(identity))
    assert controller.start(request, "fixed")["usage"]["steps"] == 2
    with pytest.raises(PermissionError, match="existing active"):
        controller.start(request)
    with pytest.raises(ValueError, match="scope"):
        controller.start(request.model_copy(update={"milestone": "other"}), "fixed")


def test_two_starts_are_serialized(engine, controller):
    def attempt(_):
        try:
            return controller.start(AutonomousRequest(milestone="same", mode="local"))["run_id"]
        except PermissionError:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        values = list(pool.map(attempt, range(2)))
    assert sum(v is not None for v in values) == 1


def test_step_budget_and_resume_remain_bounded(engine, controller):
    identity = start(controller, max_steps=1)
    value = asyncio.run(controller.run(identity))
    assert value["state"] == "PAUSED"
    calls = controller.services.calls
    again = asyncio.run(controller.resume(identity))
    assert again["state"] == "PAUSED" and controller.services.calls == calls


def test_pause_preserves_inflight_ownership(engine, controller):
    identity = start(controller)
    position(engine, identity)
    value = controller.pause(identity)
    assert value["current_operation"] == "fixture-operation"
    with pytest.raises(PermissionError, match="unfinished"):
        asyncio.run(controller.resume(identity))
    assert asyncio.run(controller.advance(identity))["state"] == "PAUSED"


@pytest.mark.parametrize("limit", ["max_invocations", "max_attempts", "max_tasks"])
def test_reservations_enforced_before_dispatch_and_rollback_atomically(engine, controller, limit):
    identity = start(controller, **{limit: 1})
    position(engine, identity)
    guard = controller.dispatch_guard(identity, "fixture-operation")

    def reserve(session, task):
        guard(
            session,
            SimpleNamespace(id=task, task_id=task),
            SimpleNamespace(timeout_seconds=1),
            SimpleNamespace(timeout_seconds=1),
        )

    with pytest.raises(BudgetExceeded):
        with transaction(engine) as session:
            reserve(session, "one")
            reserve(session, "two")
    value = report(engine, identity)
    assert value["usage"]["invocations"] == 0
    assert not any(e["kind"] == "dispatch.reserved" for e in value["events"])
    with transaction(engine) as session:
        reserve(session, "one")
    assert report(engine, identity)["usage"]["invocations"] == 1


def test_unknown_monetary_cost_blocks_before_model_dispatch(engine, controller):
    identity = start(controller, max_model_cost=1.0)
    position(engine, identity)
    with pytest.raises(BudgetExceeded, match="unknown"):
        with transaction(engine) as session:
            controller.dispatch_guard(identity, "fixture-operation")(
                session,
                SimpleNamespace(id="e", task_id="t"),
                SimpleNamespace(timeout_seconds=1),
                SimpleNamespace(timeout_seconds=1),
            )
    assert report(engine, identity)["usage"]["model_cost"] is None


def test_timeout_cannot_outlive_run_deadline(engine, controller):
    identity = start(controller, max_seconds=10)
    position(engine, identity)
    with pytest.raises(BudgetExceeded, match="timeout"):
        with transaction(engine) as session:
            controller.dispatch_guard(identity, "fixture-operation")(
                session,
                SimpleNamespace(id="e", task_id="t"),
                SimpleNamespace(timeout_seconds=11),
                SimpleNamespace(timeout_seconds=11),
            )


def test_elapsed_floor_survives_controller_restart(engine, controller):
    identity = start(controller, max_seconds=10)
    with transaction(engine) as session:
        run = session.get(AutonomousRun, identity)
        run.usage = {**run.usage, "elapsed_seconds": 11}
    other = AutonomousMilestoneController(engine, controller.settings, controller.services)
    assert asyncio.run(other.run(identity))["state"] == "PAUSED"


def test_database_history_and_request_are_immutable(engine, controller):
    identity = start(controller)
    for statement in [
        "DELETE FROM autonomous_runs",
        "UPDATE autonomous_runs SET request_hash='other'",
        "UPDATE autonomous_events SET kind='fake'",
        "DELETE FROM autonomous_events",
    ]:
        with pytest.raises(IntegrityError):
            with engine.begin() as connection:
                connection.execute(text(statement))
    assert report(engine, identity)["state"] == "PLANNED"


@pytest.mark.parametrize("value", [0, -1, float("inf"), float("nan")])
def test_invalid_limits_rejected(value):
    with pytest.raises(ValidationError):
        RunLimits(max_seconds=value)
    with pytest.raises(ValidationError):
        RunLimits(max_model_cost=value)


@pytest.mark.parametrize(
    "entries",
    [
        [{"id": "one", "depends_on": ["missing"]}],
        [{"id": "one", "depends_on": ["two"]}, {"id": "two", "depends_on": ["one"]}],
        [{"id": "one"}, {"id": "one"}],
    ],
)
def test_roadmap_unknown_duplicate_and_cyclic_dependencies_rejected(entries):
    with pytest.raises(ValidationError):
        Roadmap(milestones=entries)


def test_report_export_is_atomic_immutable_and_repairable(engine, controller, tmp_path):
    import json
    from pathlib import Path

    from agrosphere_orchestrator.autonomous_store import export_report

    identity = start(controller)
    result = export_report(engine, identity, tmp_path / "reports")
    assert export_report(engine, identity, tmp_path / "reports") == result
    source = Path(result["files"][0])
    assert json.loads(source.read_text())["run_id"] == identity
    source.unlink()
    assert export_report(engine, identity, tmp_path / "reports") == result
    source.write_text("tampered")
    with pytest.raises(ValueError, match="Immutable"):
        export_report(engine, identity, tmp_path / "reports")


def test_nonapproval_blockers_are_distinct_and_pause_reason_survives_observation(
    engine, controller
):
    identity = start(controller)
    position(engine, identity)
    value = controller._finish(
        identity,
        "fixture-operation",
        StepResult(
            next_step="EXECUTING",
            checkpoint={"category": "scheduler", "reason": "Unverified dependency"},
        ),
    )
    assert value["state"] == "BLOCKED"
    # A separate paused run retains the operator reason when a child finishes.
    other = controller.start(AutonomousRequest(milestone="other", mode="local"))["run_id"]
    position_id = "second-operation"
    with transaction(engine) as session:
        run = session.get(AutonomousRun, other)
        run.state, run.step = "EXECUTING", "EXECUTING"
        session.add(
            AutonomousOperation(
                id=position_id,
                run_id=other,
                sequence=1,
                step="EXECUTING",
                request_hash=run.request_hash,
            )
        )
        session.flush()
        run.current_operation = position_id
        run.usage = {**run.usage, "steps": 1}
    controller.pause(other)
    observed = controller._finish(other, position_id, StepResult(next_step="VERIFYING"))
    assert observed["state"] == "PAUSED"
    assert observed["checkpoint"]["category"] == "operator"
