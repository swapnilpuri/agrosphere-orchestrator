"""Versioned scheduling recommendations; execution permissions remain in AEO-2."""

from enum import StrEnum
from pathlib import PurePosixPath
from typing import Self

from pydantic import Field, model_validator

from .execution_models import ExecutionMode
from .models import Identifier, MilestoneSpec, StrictModel


class FailureKind(StrEnum):
    TRANSIENT_RUNTIME_ERROR = "TRANSIENT_RUNTIME_ERROR"
    CODE_VALIDATION_FAILURE = "CODE_VALIDATION_FAILURE"
    CONTRACT_MISMATCH = "CONTRACT_MISMATCH"
    SECURITY_POLICY_VIOLATION = "SECURITY_POLICY_VIOLATION"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    REPOSITORY_CONFLICT = "REPOSITORY_CONFLICT"
    DEPENDENCY_FAILURE = "DEPENDENCY_FAILURE"
    INVALID_AGENT_OUTPUT = "INVALID_AGENT_OUTPUT"
    EXECUTION_TIMEOUT = "EXECUTION_TIMEOUT"
    UNKNOWN_FAILURE = "UNKNOWN_FAILURE"


class ArtifactReference(StrictModel):
    repository: Identifier
    path: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    revision: str = Field(min_length=1)
    producer: Identifier | None = None

    @model_validator(mode="after")
    def relative_path(self) -> Self:
        p = PurePosixPath(self.path)
        if p.is_absolute() or ".." in p.parts or ":" in self.path or "\\" in self.path:
            raise ValueError("Artifact path must be repository relative")
        return self


class TaskOptions(StrictModel):
    mode: ExecutionMode = ExecutionMode.READ_ONLY
    allowed_paths: list[str] = Field(default_factory=lambda: ["."], min_length=1)
    inputs: list[ArtifactReference] = Field(default_factory=list)
    expected_outputs: list[str] = Field(default_factory=list)
    validation_commands: list[Identifier] = Field(default_factory=list)
    resources: list[Identifier] = Field(default_factory=list)
    priority: int = 0
    complexity: str | None = None
    specialization: str | None = None
    max_repairs: int = Field(default=3, ge=0, le=3)
    timeout_seconds: int = Field(default=300, ge=1, le=3600)
    approval_requirements: list[str] = Field(default_factory=lambda: ["design", "execution-grant"])

    @model_validator(mode="after")
    def safe_paths(self) -> Self:
        for value in [*self.allowed_paths, *self.expected_outputs]:
            p = PurePosixPath(value)
            if (
                not value
                or p.is_absolute()
                or ".." in p.parts
                or ":" in value
                or "\\" in value
                or any(c in value for c in "*?[]")
            ):
                raise ValueError("Paths must be literal repository-relative scopes")
        if self.mode == ExecutionMode.WORKTREE_WRITE and not self.validation_commands:
            raise ValueError("Write tasks require orchestrator validation commands")
        return self


class ExecutionPlan(StrictModel):
    milestone: MilestoneSpec
    version: int = Field(default=1, ge=1)
    design_revision: str
    tasks: dict[Identifier, TaskOptions]
    proposed_by: str = "project-manager"
    reviewed_by: str = "program-manager"

    @model_validator(mode="after")
    def graph(self) -> Self:
        tasks = {t.id: t for t in self.milestone.tasks}
        if set(tasks) != set(self.tasks):
            raise ValueError("Task options must exactly cover approved milestone tasks")
        for identity, options in self.tasks.items():
            for artifact in options.inputs:
                if artifact.producer:
                    if artifact.producer not in tasks[identity].depends_on:
                        raise ValueError("Artifact producer must be an explicit dependency")
                    if artifact.path not in self.tasks[artifact.producer].expected_outputs:
                        raise ValueError("Unresolved producer artifact")
                    if artifact.repository != tasks[artifact.producer].repository:
                        raise ValueError("Artifact repository differs from producer")
        return self

    def plantuml(self) -> str:
        lines = ["@startuml"]
        for index, task in enumerate(self.milestone.tasks):
            lines.append(f'object "{task.id}" as T{index}')
        ids = {t.id: i for i, t in enumerate(self.milestone.tasks)}
        for task in self.milestone.tasks:
            for dep in task.depends_on:
                lines.append(f"T{ids[dep]} --> T{ids[task.id]}")
        return "\n".join([*lines, "@enduml", ""])
