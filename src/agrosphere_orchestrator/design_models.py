"""Typed contracts for documentation agents, human review and immutable revisions."""

import re
from enum import StrEnum
from typing import Literal, Self

from pydantic import Field, model_validator

from .models import Identifier, MilestoneSpec, StrictModel


class MilestoneState(StrEnum):
    DISCOVERED = "DISCOVERED"
    DESIGN_IN_PROGRESS = "DESIGN_IN_PROGRESS"
    DESIGN_VALIDATING = "DESIGN_VALIDATING"
    AWAITING_DESIGN_APPROVAL = "AWAITING_DESIGN_APPROVAL"
    DESIGN_APPROVED = "DESIGN_APPROVED"
    IMPLEMENTATION_READY = "IMPLEMENTATION_READY"
    IMPLEMENTING = "IMPLEMENTING"
    IMPLEMENTATION_VALIDATING = "IMPLEMENTATION_VALIDATING"
    AWAITING_DELIVERY_APPROVAL = "AWAITING_DELIVERY_APPROVAL"
    COMPLETED = "COMPLETED"


class Requirement(StrictModel):
    id: Identifier
    text: str = Field(min_length=1)
    acceptance_criteria: list[str] = Field(min_length=1)


class ContextReference(StrictModel):
    repository: Identifier
    path: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    head: str | None = None


class DiagramNode(StrictModel):
    id: str = Field(pattern=r"^[A-Za-z][A-Za-z0-9_]*$")
    label: str = Field(min_length=1, max_length=200)


class DiagramEdge(StrictModel):
    source: str
    target: str
    label: str = Field(min_length=1, max_length=200)


DiagramKind = Literal[
    "context",
    "container",
    "component",
    "sequence",
    "domain",
    "activity",
    "state",
    "data-flow",
    "deployment",
]


class DiagramSpec(StrictModel):
    id: Identifier
    kind: DiagramKind
    repository: Identifier
    requirement_ids: list[Identifier] = Field(min_length=1)
    nodes: list[DiagramNode] = Field(min_length=1)
    edges: list[DiagramEdge] = Field(default_factory=list)
    rationale: str = Field(min_length=1)
    # Exact approved source takes precedence over the graph template. It is rendered and
    # checked by the same safe local renderer, and included in the requirements digest.
    approved_source: str | None = Field(default=None, min_length=1, max_length=200_000)

    @model_validator(mode="after")
    def graph(self) -> Self:
        ids = {n.id for n in self.nodes}
        if len(ids) != len(self.nodes) or any(
            e.source not in ids or e.target not in ids for e in self.edges
        ):
            raise ValueError("duplicate node or unknown diagram endpoint")
        return self


class ContractProposal(StrictModel):
    id: Identifier
    kind: Literal["openapi", "event-schema"]
    content: str = Field(min_length=1)
    requirement_ids: list[Identifier] = Field(min_length=1)
    version: str = Field(min_length=1)


class DesignInput(StrictModel):
    documentation_scope: Literal["application", "internal-orchestrator"] = "application"
    plan: MilestoneSpec
    requirements: list[Requirement] = Field(min_length=1)
    context: list[ContextReference] = Field(min_length=1)
    # Narratives are supplied approved material, never inferred business requirements.
    narratives: dict[str, dict[str, str]] = Field(default_factory=dict)
    diagrams: list[DiagramSpec] = Field(default_factory=list)
    contracts: list[ContractProposal] = Field(default_factory=list)
    contract_impact: bool = False

    @model_validator(mode="after")
    def references(self) -> Self:
        if self.documentation_scope == "internal-orchestrator":
            owners = {t.repository for t in self.plan.tasks}
            owners |= {c.repository for c in self.context}
            owners |= {d.repository for d in self.diagrams}
            if owners != {"agrosphere-orchestrator"} or self.contract_impact or self.contracts:
                raise ValueError(
                    "Internal documentation requires orchestrator-only scope without contracts"
                )
        ids = {r.id for r in self.requirements}
        if len(ids) != len(self.requirements):
            raise ValueError("duplicate requirement IDs")
        for artifact in [*self.diagrams, *self.contracts]:
            if not set(artifact.requirement_ids) <= ids:
                raise ValueError("unknown artifact requirement reference")
        keys = [d.id for d in self.diagrams] + [c.id for c in self.contracts]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate diagram/contract IDs")
        return self


class Artifact(StrictModel):
    type: str
    repository: Identifier
    path: str
    content: str
    sha256: str
    requirement_ids: list[Identifier]
    agent: Identifier
    generated_at: str = ""


class Finding(StrictModel):
    code: str
    message: str
    severity: Literal["error", "warning", "info"] = "error"
    artifact: str | None = None


class AgentResult(StrictModel):
    artifacts: list[Artifact] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)


class DocumentationTask(StrictModel):
    role: Identifier
    phase: Literal["design", "as-built"]
    milestone: str
    scope_digest: str


class AsBuiltInput(StrictModel):
    narratives: dict[str, dict[str, str]]
    context: list[ContextReference] = Field(min_length=1)
    diagrams: list[DiagramSpec] = Field(min_length=1)
    contracts: list[ContractProposal] = Field(default_factory=list)


def case_key(project: str, milestone: str) -> str:
    # Both components must satisfy the existing identifier constraint.
    for value in (project, milestone):
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", value):
            raise ValueError("invalid project or milestone identifier")
    return project + ":" + milestone
