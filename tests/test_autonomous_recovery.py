"""Every documented interruption category retains intent and prohibits blind replay."""

import asyncio

import pytest
from test_autonomous import Ports, position, start

from agrosphere_orchestrator.autonomous import AutonomousMilestoneController
from agrosphere_orchestrator.autonomous_models import RECOVERY_BOUNDARIES, StepResult
from agrosphere_orchestrator.autonomous_store import report
from agrosphere_orchestrator.config.settings import Settings


@pytest.mark.parametrize("scenario", RECOVERY_BOUNDARIES)
def test_uncertain_boundary_never_redispatches_and_requires_verified_child_outcome(
    engine, scenario
):
    ports = Ports()
    controller = AutonomousMilestoneController(engine, Settings(_env_file=None), ports)
    identity = start(controller)
    stages = {
        "discovery": "RECONCILING",
        "documentation": "PREPARING_DESIGN",
        "before-design-approval": "PREPARING_DESIGN",
        "after-approval": "PLANNING_TASKS",
        "task-decomposition": "PLANNING_TASKS",
        "quality": "VERIFYING",
        "remediation": "VERIFYING",
        "before-publication": "PREPARING_DELIVERY",
        "publication-response-lost": "OBSERVING_DELIVERY",
        "external-ci-change": "OBSERVING_DELIVERY",
    }
    stage = stages.get(scenario, "EXECUTING")
    position(engine, identity, stage)
    first = asyncio.run(controller.recover(identity))
    assert first["state"] == "RECOVERY_REQUIRED"
    assert first["current_operation"] == "fixture-operation"
    assert ports.calls == 0
    assert asyncio.run(controller.advance(identity))["current_operation"] == "fixture-operation"
    with pytest.raises(PermissionError):
        asyncio.run(controller.resume(identity))
    # An independently observed outcome can be adopted once, preserving prior intent.
    ports.recovered = StepResult(next_step=stage, evidence={"fixture_verified_boundary": scenario})
    recovered = asyncio.run(controller.recover(identity))
    assert recovered["current_operation"] is None
    assert len([e for e in recovered["events"] if e["kind"] == "operation.committed"]) == 1
    assert asyncio.run(controller.recover(identity))["usage"] == recovered["usage"]


@pytest.mark.parametrize(
    "boundary",
    ["after-intent", "before-dispatch", "after-observation", "before-commit", "after-commit"],
)
def test_fault_injection_preserves_exact_once_adoption(engine, boundary):
    def fault(point, operation):
        if point == boundary:
            raise RuntimeError("Simulated power loss")

    ports = Ports()
    controller = AutonomousMilestoneController(engine, Settings(_env_file=None), ports, fault)
    identity = start(controller)
    with pytest.raises(RuntimeError):
        asyncio.run(controller.advance(identity))
    value = report(engine, identity)
    assert value["usage"]["steps"] == 1
    other = AutonomousMilestoneController(engine, Settings(_env_file=None), ports)
    if boundary == "after-commit":
        assert value["current_operation"] is None
        assert value["step"] == "PREPARING_DESIGN"
    else:
        assert value["current_operation"]
        calls = ports.calls
        asyncio.run(other.advance(identity))
        assert ports.calls == calls
        ports.recovered = StepResult(next_step="PREPARING_DESIGN", evidence={"observed": True})
        assert asyncio.run(other.recover(identity))["current_operation"] is None
