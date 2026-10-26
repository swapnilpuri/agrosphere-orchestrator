"""Strict contracts for one bounded, explicitly selected AgroSphere milestone."""

from enum import StrEnum

from pydantic import Field, model_validator

from .delivery_models import Manifest
from .design_models import DesignInput
from .models import Identifier, StrictModel
from .orchestration_models import TaskOptions


class RunState(StrEnum):
    PLANNED = "PLANNED"
    RECONCILING = "RECONCILING"
    PREPARING_DESIGN = "PREPARING_DESIGN"
    PLANNING_TASKS = "PLANNING_TASKS"
    EXECUTING = "EXECUTING"
    VERIFYING = "VERIFYING"
    PREPARING_DELIVERY = "PREPARING_DELIVERY"
    OBSERVING_DELIVERY = "OBSERVING_DELIVERY"
    REPORTED = "REPORTED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    PAUSED = "PAUSED"
    BLOCKED = "BLOCKED"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"


STEPS = (
    "RECONCILING",
    "PREPARING_DESIGN",
    "PLANNING_TASKS",
    "EXECUTING",
    "VERIFYING",
    "PREPARING_DELIVERY",
    "OBSERVING_DELIVERY",
    "REPORTED",
)
RECOVERY_BOUNDARIES = (
    "discovery",
    "documentation",
    "before-design-approval",
    "after-approval",
    "task-decomposition",
    "agent-execution",
    "child-finished",
    "parallel-scheduling",
    "quality",
    "remediation",
    "before-publication",
    "publication-response-lost",
    "external-ci-change",
    "changed-approved-artifacts",
    "revoked-approval",
    "repository-conflict",
)


class RunLimits(StrictModel):
    max_milestones: int = Field(default=1, ge=1, le=1)
    max_tasks: int = Field(default=20, ge=1, le=1000)
    max_concurrency: int = Field(default=2, ge=1, le=32)
    max_invocations: int = Field(default=30, ge=1, le=10000)
    max_attempts: int = Field(default=30, ge=1, le=10000)
    max_repairs: int = Field(default=3, ge=0, le=3)
    max_seconds: int = Field(default=3600, ge=1, le=86400)
    max_poll_seconds: int = Field(default=60, ge=0, le=300)
    max_steps: int = Field(default=50, ge=1, le=1000)
    max_model_cost: float | None = Field(default=None, gt=0, allow_inf_nan=False)


class AutonomousRequest(StrictModel):
    milestone: Identifier
    mode: str = Field(default="dry-run", pattern=r"^(dry-run|local|controlled-delivery)$")
    requirements: DesignInput | None = None
    task_options: dict[str, TaskOptions] | None = None
    delivery_manifest: Manifest | None = None
    # Exact previously authenticated AEO-5 grants, keyed by unit:action.
    publication_grants: dict[str, str] = Field(default_factory=dict)
    limits: RunLimits = Field(default_factory=RunLimits)

    @model_validator(mode="after")
    def scope(self):
        if self.requirements and (
            self.requirements.plan.project != "agrosphere"
            or self.requirements.plan.id != self.milestone
        ):
            raise ValueError("Requirements do not match selected AgroSphere milestone")
        if self.delivery_manifest and (
            self.delivery_manifest.project != "agrosphere"
            or self.delivery_manifest.milestone != self.milestone
        ):
            raise ValueError("Delivery does not match selected milestone")
        return self


class StepResult(StrictModel):
    next_step: str
    evidence: dict = Field(default_factory=dict)
    checkpoint: dict | None = None

    @model_validator(mode="after")
    def known(self):
        if self.next_step not in STEPS:
            raise ValueError("Unknown autonomous transition")
        return self


class BudgetExceeded(PermissionError):
    pass


class RoadmapEntry(StrictModel):
    id: Identifier
    depends_on: list[Identifier] = Field(default_factory=list)


class Roadmap(StrictModel):
    milestones: list[RoadmapEntry] = Field(min_length=1)

    @model_validator(mode="after")
    def dag(self):
        graph = {m.id: m.depends_on for m in self.milestones}
        if len(graph) != len(self.milestones):
            raise ValueError("Duplicate roadmap milestones")
        active, seen = set(), set()

        def visit(key):
            if key not in graph or key in active:
                raise ValueError("Unknown or cyclic roadmap dependency")
            if key in seen:
                return
            active.add(key)
            if len(graph[key]) != len(set(graph[key])):
                raise ValueError("Duplicate roadmap dependency")
            for dependency in graph[key]:
                visit(dependency)
            active.remove(key)
            seen.add(key)

        for key in graph:
            visit(key)
        return self
