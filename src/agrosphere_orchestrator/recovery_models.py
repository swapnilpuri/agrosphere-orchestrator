"""Observed recovery state is independent of imported plans and approvals."""

from typing import Literal

from pydantic import Field

from .models import StrictModel
from .persistence import now

Classification = Literal["COMPLETED", "PARTIAL", "NOT_STARTED", "UNVERIFIED"]


class Evidence(StrictModel):
    repository: str
    path: str
    kind: Literal["document", "commit", "test-result"]
    sha256: str
    head: str | None = None
    modified_at: str | None = None
    line: int | None = None
    excerpt: str = ""
    outcome: str | None = None


class RecoveredMilestone(StrictModel):
    id: str
    classification: Classification = "UNVERIFIED"
    confidence: Literal["low", "medium", "high"] = "low"
    objectives: list[str] = Field(default_factory=list)
    implementation: list[str] = Field(default_factory=list)
    repositories: list[str] = Field(default_factory=list)
    tests: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    verified_acceptance_criteria: list[str] = Field(default_factory=list)
    outstanding: list[str] = Field(default_factory=list)
    missing_documentation: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)


class RecoverySnapshot(StrictModel):
    schema_version: int = 1
    workspace: str
    observed_at: str = Field(default_factory=now)
    repositories: list[dict]
    missing_repositories: list[str] = Field(default_factory=list)
    milestones: list[RecoveredMilestone]
    limitations: list[str] = Field(default_factory=list)
