"""Serial documentation-role adapters. No live models, Codex calls or code execution."""

import re
from typing import Protocol

from .design_artifacts import digest, plantuml
from .design_models import AgentResult, Artifact, DesignInput, DocumentationTask, Finding
from .design_policy import architecture_owner, service_owners

SECTIONS = {
    "business": (
        "Business context",
        "Problem statement",
        "Objectives",
        "User stories",
        "Functional requirements",
        "Nonfunctional requirements",
        "Acceptance criteria",
    ),
    "architecture": (
        "Architecture overview",
        "Impacted microservices",
        "DDD boundaries",
        "APIs and event interactions",
        "Database changes",
        "Security considerations",
        "Technology decisions",
        "Architectural trade-offs",
        "Risks and assumptions",
        "Architectural decisions",
        "Integration design",
    ),
    "overview": (
        "Milestone overview",
        "What will be built",
        "Why it is needed",
        "Platform fit",
        "Component responsibilities",
        "Implementation sequence",
        "Expected outcomes",
        "User-facing documentation",
    ),
    "service": (
        "Technical design",
        "Domain model",
        "Interfaces",
        "Persistence",
        "Security",
        "Developer documentation",
    ),
    "contracts": ("Proposed APIs", "Proposed versioned events", "Compatibility analysis"),
    "as-built": (
        "As-built architecture",
        "API and event documentation",
        "Technical design",
        "Relevant ADRs",
        "Implementation notes",
        "Known limitations",
        "Validation evidence",
    ),
}
ROLES = ("business-analyst", "solution-architect", "technical-writer")


class DocumentationAgents(Protocol):
    version: str

    def generate(self, task: DocumentationTask, inputs: DesignInput) -> AgentResult: ...


class ArchitectureReviewer(Protocol):
    version: str

    def review(self, inputs: DesignInput, artifacts: list[Artifact]) -> list[Finding]: ...


class TemplateDocumentationAgents:
    """Render approved narratives verbatim. Missing knowledge is an explicit blocker."""

    version = "approved-input-templates-v3-internal-narrative"

    def generate(self, task: DocumentationTask, inputs: DesignInput) -> AgentResult:
        result = AgentResult()
        refs = [r.id for r in inputs.requirements]
        services = sorted(service_owners(inputs))
        owner = architecture_owner(inputs)
        documents = []
        if task.phase == "design":
            if task.role == "business-analyst":
                documents.append(("business", owner, "business"))
            if task.role == "solution-architect":
                documents.append(("architecture", owner, "architecture"))
                documents.extend(("service", repo, "service:" + repo) for repo in services)
                if inputs.contract_impact:
                    documents.append(("contracts", "agrosphere-contracts", "contracts"))
            if task.role == "technical-writer":
                documents.append(("overview", owner, "overview"))
        elif task.role == "solution-architect":
            documents.append(("as-built", owner, "as-built"))
            documents.extend(("service", repo, "service:" + repo) for repo in services)
            if inputs.contract_impact:
                documents.append(("contracts", "agrosphere-contracts", "contracts"))
        elif task.role == "technical-writer":
            documents.append(("overview", owner, "overview"))
        for kind, repo, key in documents:
            supplied = inputs.narratives.get(key, {})
            # Internal scope has exactly one service owner. Reuse its approved generic
            # narrative only when no repository-specific narrative was supplied.
            if (
                kind == "service"
                and inputs.documentation_scope == "internal-orchestrator"
                and key not in inputs.narratives
            ):
                supplied = inputs.narratives.get("service", {})
            content = (
                f"# {inputs.plan.id}: {kind} ({task.phase})\n\n"
                f"Scope: {task.scope_digest}\nRequirements: {', '.join(refs)}\n"
            )
            for section in SECTIONS[kind]:
                text = supplied.get(section, "").strip()
                if kind == "business" and section in {
                    "Functional requirements",
                    "Acceptance criteria",
                }:
                    text = "\n".join(
                        f"- {r.id}: {r.text}"
                        + (
                            " — " + "; ".join(r.acceptance_criteria)
                            if section == "Acceptance criteria"
                            else ""
                        )
                        for r in inputs.requirements
                    )
                if not text:
                    text = "MISSING: approved information required."
                    result.findings.append(
                        Finding(code="missing-information", message=f"{key}: {section}")
                    )
                content += f"\n## {section}\n\n{text}\n"
            content += "\n## Verified context references\n\n" + "\n".join(
                f"- {c.repository}/{c.path} sha256={c.sha256} HEAD={c.head}" for c in inputs.context
            )
            result.artifacts.append(
                Artifact(
                    type=kind,
                    repository=repo,
                    path=kind + ".md",
                    content=content + "\n",
                    sha256=digest(content + "\n"),
                    requirement_ids=refs,
                    agent=task.role,
                )
            )
        if task.role == "solution-architect":
            for spec in inputs.diagrams:
                source = (
                    spec.approved_source if spec.approved_source is not None else plantuml(spec)
                )
                result.artifacts.append(
                    Artifact(
                        type="diagram:" + spec.kind,
                        repository=spec.repository,
                        path=f"diagrams/{spec.id}.puml",
                        content=source,
                        sha256=digest(source),
                        requirement_ids=spec.requirement_ids,
                        agent=task.role,
                    )
                )
            for proposal in inputs.contracts:
                result.artifacts.append(
                    Artifact(
                        type="proposal:" + proposal.kind,
                        repository="agrosphere-contracts",
                        path=f"proposals/{proposal.id}-{proposal.version}.yaml",
                        content=proposal.content,
                        sha256=digest(proposal.content),
                        requirement_ids=proposal.requirement_ids,
                        agent=task.role,
                    )
                )
        return result


class RuleBasedArchitectureReviewer:
    """Independent role task with deliberately limited conceptual checks, not an LLM opinion."""

    version = "independent-rule-review-v2-approved-source"

    def review(self, inputs: DesignInput, artifacts: list[Artifact]) -> list[Finding]:
        findings = [
            Finding(
                code="review-limit",
                severity="warning",
                message="Independent rule review checks declared scope and references; human conceptual review remains mandatory.",
            )
        ]
        impacted = {t.repository for t in inputs.plan.tasks}
        represented = {a.repository for a in artifacts}
        for repo in impacted - represented:
            findings.append(
                Finding(
                    code="review-scope",
                    message=f"No design artifact for impacted repository {repo}",
                )
            )
        for diagram in inputs.diagrams:
            if diagram.kind not in {"sequence", "data-flow"}:
                continue
            # The approved source replaces generated nodes/edges. Inspect that same
            # representation, retaining the mandatory interaction check.
            has_interactions = bool(diagram.edges)
            if diagram.approved_source is not None:
                has_interactions = source_has_interactions(diagram.approved_source)
            if not has_interactions:
                findings.append(
                    Finding(
                        code="review-interactions",
                        message=f"{diagram.id}: interaction diagram has no interactions",
                    )
                )
        return findings


def source_has_interactions(source: str) -> bool:
    """Recognize explicit labelled PlantUML messages, excluding comments and notes."""
    endpoint = r'(?:[A-Za-z_][A-Za-z0-9_]*|"[^"\n]+")'
    message = re.compile(rf"^\s*{endpoint}\s+(?:-+>|<-+|\.+>|<\.+)\s+{endpoint}\s*:\s*\S")
    in_comment = False
    in_note = False
    for line in source.splitlines():
        stripped = line.strip()
        if in_comment:
            if "'/" in stripped:
                in_comment = False
            continue
        if stripped.startswith("/'"):
            in_comment = "'/" not in stripped[2:]
            continue
        if stripped.startswith("'"):
            continue
        if in_note:
            if stripped.lower() in {"end note", "end rnote", "end hnote"}:
                in_note = False
            continue
        if re.match(r"^(?:note|rnote|hnote)\b", stripped, re.I):
            in_note = ":" not in stripped
            continue
        if message.match(line):
            return True
    return False
