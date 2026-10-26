"""The parent budget hook shares the real scheduler claim transaction."""

import asyncio

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_autonomous import position
from test_design import HumanFixture
from test_design import design_workspace as design_workspace
from test_orchestration import orchestration_fixture as orchestration_fixture
from test_orchestration import scheduler

from agrosphere_orchestrator.autonomous import AutonomousMilestoneController
from agrosphere_orchestrator.autonomous_models import AutonomousRequest, BudgetExceeded, RunLimits
from agrosphere_orchestrator.autonomous_store import report
from agrosphere_orchestrator.execution import approve_execution
from agrosphere_orchestrator.orchestration_store import ResourceLease, TaskClaim


def test_real_scheduler_cannot_launch_when_parent_budget_refuses_claim(
    engine, orchestration_fixture
):
    f = orchestration_fixture
    controller = AutonomousMilestoneController(engine, f.settings)
    value = controller.start(
        AutonomousRequest(milestone="FIXTURE-1", mode="local", limits=RunLimits(max_model_cost=1))
    )
    identity = value["run_id"]
    position(engine, identity)
    service = scheduler(engine, f)

    async def batch():
        for execution in await service.prepare("FIXTURE-1", "fixture"):
            approve_execution(engine, f.settings, execution, HumanFixture())
        await service.execute_ready_tasks(
            "FIXTURE-1",
            "fixture",
            dispatch_guard=controller.dispatch_guard(identity, "fixture-operation"),
        )

    with pytest.raises(BudgetExceeded, match="unknown"):
        asyncio.run(batch())
    assert service.adapter.calls == 0
    with Session(engine) as session:
        assert not list(session.scalars(select(TaskClaim)))
        assert not list(session.scalars(select(ResourceLease)))
    assert report(engine, identity)["usage"]["invocations"] == 0


def test_real_scheduler_honors_parent_batch_cap_and_reservations(engine, orchestration_fixture):
    f = orchestration_fixture
    controller = AutonomousMilestoneController(engine, f.settings)
    identity = controller.start(
        AutonomousRequest(milestone="FIXTURE-1", mode="local", limits=RunLimits(max_concurrency=1))
    )["run_id"]
    position(engine, identity)
    service = scheduler(engine, f)
    batches = []

    async def workflow():
        for _ in range(12):
            for execution in await service.prepare("FIXTURE-1", "fixture"):
                approve_execution(engine, f.settings, execution, HumanFixture())
            value = await service.execute_ready_tasks(
                "FIXTURE-1",
                "fixture",
                dispatch_guard=controller.dispatch_guard(identity, "fixture-operation"),
                max_batch_size=1,
            )
            batches.append(value)
            if not value["results"]:
                break

    asyncio.run(workflow())
    assert all(len(b["results"]) <= 1 for b in batches)
    assert report(engine, identity)["usage"]["invocations"] == service.adapter.calls == 10
