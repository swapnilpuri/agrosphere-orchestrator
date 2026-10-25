"""Language-neutral governance contracts. Commands are administrator-owned IDs."""

from enum import StrEnum
from typing import Literal, Self

from pydantic import Field, model_validator

from .models import Identifier, StrictModel


class GateState(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"


class Severity(StrEnum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFORMATIONAL = "INFORMATIONAL"


class ApprovalCategory(StrEnum):
    DESIGN_APPROVAL = "DESIGN_APPROVAL"
    ARCHITECTURE_CHANGE = "ARCHITECTURE_CHANGE"
    CONTRACT_BREAKING_CHANGE = "CONTRACT_BREAKING_CHANGE"
    SECURITY_EXCEPTION = "SECURITY_EXCEPTION"
    DEPENDENCY_EXCEPTION = "DEPENDENCY_EXCEPTION"
    PRIVILEGED_EXECUTION = "PRIVILEGED_EXECUTION"
    DELIVERY_APPROVAL = "DELIVERY_APPROVAL"
    DEPLOYMENT_APPROVAL = "DEPLOYMENT_APPROVAL"


class Finding(StrictModel):
    id: Identifier
    message: str = Field(min_length=1)
    severity: Severity = Severity.HIGH
    location: str | None = None


class ArchitectureRule(StrictModel):
    id: Identifier
    repository: Identifier
    path: str
    kind: Literal[
        "required-file",
        "prohibited-file",
        "required-token",
        "prohibited-token",
        "approved-hash",
        "database-owner",
    ]
    value: str = ""


class Gate(StrictModel):
    id: Identifier
    type: Literal[
        "build",
        "test",
        "lint",
        "types",
        "coverage",
        "security",
        "architecture",
        "contract",
        "documentation",
        "database",
        "infrastructure",
    ]
    repository: Identifier
    tasks: list[Identifier] = Field(default_factory=list)
    milestones: list[Identifier] = Field(default_factory=list)
    inputs: list[str] = Field(default_factory=list)
    command: Identifier | None = None
    evaluator: Literal["command", "files", "architecture", "execution"] = "command"
    format: Literal["exit", "json", "junit", "coverage", "sarif"] = "exit"
    expected_exit: int = 0
    severity: Severity = Severity.HIGH
    blocking: bool = True
    timeout_seconds: int = Field(default=120, ge=1, le=600)
    retry_eligible: bool = False
    allow_skip: bool = False
    skip: bool = False
    minimum_coverage: float | None = Field(default=None, ge=0, le=100)
    required_files: list[str] = Field(default_factory=list)
    architecture_rules: list[ArchitectureRule] = Field(default_factory=list)
    validator_version: str = Field(min_length=1)
    configuration: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def constraints(self) -> Self:
        if self.skip and not self.allow_skip:
            raise ValueError("SKIPPED requires explicit policy permission")
        if self.type == "security" and (
            not self.blocking or self.allow_skip or self.format not in {"json", "sarif"}
        ):
            raise ValueError("Security gates require blocking structured scanner evidence")
        if self.type == "coverage" and (self.minimum_coverage is None or self.format != "coverage"):
            raise ValueError("Coverage gates require threshold and coverage format")
        if self.evaluator == "files" and (not self.required_files or self.type != "documentation"):
            raise ValueError("File evaluator only validates explicit documentation requirements")
        if self.evaluator == "architecture" and (
            self.type != "architecture" or not self.architecture_rules
        ):
            raise ValueError("Architecture evaluator requires explicit boundary rules")
        if self.evaluator in {"command", "execution"} and not self.command:
            raise ValueError("Command gate requires an allowlisted command ID")
        if self.type == "security" and self.retry_eligible:
            raise ValueError("Security findings require explicit reviewer escalation")
        return self


class Criterion(StrictModel):
    requirement_id: Identifier
    criterion_id: Identifier
    criterion_text: str = Field(min_length=1)
    task: Identifier
    gate: Identifier | None = None
    test_case: str | None = None
    human: bool = False


class QualityPolicy(StrictModel):
    id: Identifier
    version: int = Field(ge=1)
    gates: list[Gate] = Field(min_length=1)
    criteria: list[Criterion] = Field(default_factory=list)
    evidence_ttl_seconds: int = Field(default=86400, ge=1, le=2592000)
    medium_security_blocks: bool = True
    required_gate_types: list[str] = Field(
        default_factory=lambda: [
            "build",
            "test",
            "security",
            "architecture",
            "contract",
            "documentation",
        ]
    )
    required_review_roles: list[str] = Field(
        default_factory=lambda: [
            "qa-engineer",
            "security-engineer",
            "solution-architect",
            "technical-writer",
        ]
    )

    @model_validator(mode="after")
    def references(self) -> Self:
        ids = [g.id for g in self.gates]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate gate IDs")
        keys = [(c.requirement_id, c.criterion_id) for c in self.criteria]
        if len(keys) != len(set(keys)):
            raise ValueError("Duplicate acceptance criterion mapping")
        if any(c.gate not in ids for c in self.criteria if not c.human):
            raise ValueError("Criterion must reference a policy gate")
        return self


class GateResult(StrictModel):
    gate_id: str
    execution_id: str
    repository: str
    artifact_hash: str
    validator_version: str
    command: list[str] = Field(default_factory=list)
    exit_code: int | None = None
    started_at: str
    ended_at: str
    findings: list[Finding] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    state: GateState
    policy_version: int
    test_cases: dict[str, str] = Field(default_factory=dict)
    coverage: float | None = None
    details: dict = Field(default_factory=dict)
