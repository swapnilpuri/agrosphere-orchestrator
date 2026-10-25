"""Transport-neutral, typed single-task execution contracts."""

from enum import StrEnum
from pathlib import PurePosixPath
from typing import Self
from uuid import uuid4

from pydantic import Field, model_validator

from .models import Identifier, StrictModel


class ExecutionMode(StrEnum):
    READ_ONLY = "READ_ONLY"
    WORKTREE_WRITE = "WORKTREE_WRITE"
    VALIDATION_ONLY = "VALIDATION_ONLY"


class ExecutionState(StrEnum):
    QUEUED = "QUEUED"
    PREPARING = "PREPARING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    CANCELLED = "CANCELLED"
    INTERRUPTED = "INTERRUPTED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"


class RetryConfiguration(StrictModel):
    max_attempts: int = Field(default=1, ge=1, le=3)
    # Retries require a new human grant; no automatic repeated writes.
    backoff_seconds: float = Field(default=0, ge=0, le=30)


class InputArtifact(StrictModel):
    repository: Identifier
    path: str
    sha256: str
    revision: str | None = None
    content: str = ""


class ExecutionRequest(StrictModel):
    project_id: Identifier
    milestone_id: Identifier
    task_id: str
    agent_role: Identifier
    specialization: str | None = None
    repository: Identifier
    worktree_path: str
    allowed_file_scopes: list[str] = Field(min_length=1)
    required_input_artifacts: list[InputArtifact] = Field(default_factory=list)
    instructions: str = Field(min_length=1, max_length=64000)
    role_instructions: str = ""
    acceptance_criteria: list[str] = Field(min_length=1)
    mode: ExecutionMode = ExecutionMode.READ_ONLY
    approval_reference: str | None = None
    timeout_seconds: int = Field(default=300, ge=1, le=3600)
    retry: RetryConfiguration = Field(default_factory=RetryConfiguration)
    correlation_id: str = Field(default_factory=lambda: str(uuid4()))
    validation_commands: list[Identifier] = Field(default_factory=list)
    source_head: str
    context_digest: str
    design_revision: str
    parent_execution_id: str | None = None
    continuation_session_id: str | None = None

    @model_validator(mode="after")
    def safe_scopes(self) -> Self:
        for scope in self.allowed_file_scopes:
            value = PurePosixPath(scope)
            if (
                value.is_absolute()
                or ".." in value.parts
                or ":" in scope
                or "\\" in scope
                or any(c in scope for c in "*?[]")
            ):
                raise ValueError("Scopes must be literal repository-relative files or directories")
        return self


class AgentOutput(StrictModel):
    summary: str
    work_performed: list[str]
    files_changed: list[str]
    artifacts_created: list[str]
    commands_executed: list[str]
    validation_evidence: list[str]
    errors: list[str]
    warnings: list[str]
    unresolved_issues: list[str]
    suggested_next_actions: list[str]


class ExecutionError(StrictModel):
    code: str
    message: str
    retryable: bool = False


class ExecutionResult(StrictModel):
    execution_id: str
    task_id: str
    agent_role: str
    session_id: str | None = None
    status: ExecutionState
    started_at: str
    ended_at: str
    duration_seconds: float
    summary: str = ""
    changed_files: list[str] = Field(default_factory=list)
    generated_artifacts: list[str] = Field(default_factory=list)
    logs: list[str] = Field(default_factory=list)
    exit_code: int | None = None
    error: ExecutionError | None = None
    usage: dict = Field(default_factory=dict)
    validation_results: list[dict] = Field(default_factory=list)
    implementation_verified: bool = False
    evidence_references: list[str] = Field(default_factory=list)
    output: AgentOutput | None = None
    estimated_cost: float | None = None


class HealthStatus(StrictModel):
    executable: str | None = None
    version: str | None = None
    authenticated: bool = False
    exec_supported: bool = False
    mcp_supported: bool = False
    selected_transport: str | None = None
    findings: list[str] = Field(default_factory=list)
    probes: list[dict] = Field(default_factory=list)


class ValidationCommand(StrictModel):
    id: Identifier
    argv: list[str] = Field(min_length=1)
    timeout_seconds: int = Field(default=120, ge=1, le=600)


class ExecutionPolicy(StrictModel):
    live_enabled: bool = False
    timeout_limit_seconds: int = Field(default=600, ge=1, le=3600)
    max_context_bytes: int = Field(default=100000, ge=1000, le=500000)
    max_log_bytes: int = Field(default=2000000, ge=1000, le=10000000)
    max_artifact_bytes: int = Field(default=32000000, ge=1000, le=100000000)
    validation_commands: list[ValidationCommand] = Field(default_factory=list)
    input_price_per_million: float | None = Field(default=None, ge=0)
    output_price_per_million: float | None = Field(default=None, ge=0)
    trace_metadata: bool = False

    @model_validator(mode="after")
    def unique_commands(self) -> Self:
        ids = [c.id for c in self.validation_commands]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate validation command IDs")
        return self

