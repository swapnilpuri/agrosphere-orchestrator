"""Single-writer documentation lifecycle. All state and audit writes share transactions."""

import json
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from .design_agents import ROLES, ArchitectureReviewer, DocumentationAgents
from .design_artifacts import DiagramRenderer, check_files, digest, write_artifacts
from .design_models import (
    Artifact,
    AsBuiltInput,
    DesignInput,
    DocumentationTask,
    Finding,
    MilestoneState,
    case_key,
)
from .design_validation import deterministic_findings, verify_context
from .human_approval import HumanVerifier
from .persistence import (
    DesignCase,
    DesignDecision,
    DesignRevision,
    DesignScope,
    DesignValidation,
    Milestone,
    Task,
    audit,
    now,
)

S = MilestoneState
EDGES = {
    S.DISCOVERED: {S.DESIGN_IN_PROGRESS},
    S.DESIGN_IN_PROGRESS: {S.DESIGN_VALIDATING},
    S.DESIGN_VALIDATING: {S.DESIGN_IN_PROGRESS, S.AWAITING_DESIGN_APPROVAL},
    S.AWAITING_DESIGN_APPROVAL: {S.DESIGN_IN_PROGRESS, S.DESIGN_APPROVED},
    S.DESIGN_APPROVED: {S.DESIGN_IN_PROGRESS, S.IMPLEMENTATION_READY},
    S.IMPLEMENTATION_READY: {S.DESIGN_IN_PROGRESS, S.IMPLEMENTING},
    S.IMPLEMENTING: {S.IMPLEMENTATION_VALIDATING},
    S.IMPLEMENTATION_VALIDATING: {S.AWAITING_DELIVERY_APPROVAL},
    S.AWAITING_DELIVERY_APPROVAL: {S.IMPLEMENTATION_VALIDATING, S.COMPLETED},
    S.COMPLETED: set(),
}


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def move(session: Session, case: DesignCase, target: MilestoneState, actor: str = "orchestrator"):
    source = S(case.state)
    if target == source:
        return
    if target not in EDGES[source]:
        raise ValueError(f"Invalid milestone transition: {source} -> {target}")
    case.state = target.value
    audit(
        session, case.id, "design.transitioned", actor, {"from": source.value, "to": target.value}
    )


def register_requirements(
    engine: Engine, inputs: DesignInput, manifest: Path, registry: Path
) -> str:
    inputs = DesignInput.model_validate(inputs.model_dump())
    repositories = verify_context(inputs, manifest, registry)
    key = case_key(inputs.plan.project, inputs.plan.id)
    payload = {"input": inputs.model_dump(mode="json"), "repositories": repositories}
    identity = digest(canonical(payload))
    with Session(engine) as session, session.begin():
        case = session.get(DesignCase, key)
        if case is None:
            case = DesignCase(
                id=key,
                project_id=inputs.plan.project,
                external_id=inputs.plan.id,
                state=S.DISCOVERED.value,
            )
            session.add(case)
            session.flush()
        if case.scope_id == identity:
            return identity
        if S(case.state) in {
            S.IMPLEMENTING,
            S.IMPLEMENTATION_VALIDATING,
            S.AWAITING_DELIVERY_APPROVAL,
            S.COMPLETED,
        }:
            raise ValueError(
                "Active/completed implementation scope is immutable; use a new milestone"
            )
        if session.get(DesignScope, identity) is None:
            session.add(DesignScope(id=identity, case_id=key, payload=payload))
        case.scope_id = identity
        case.revision_id = None
        case.validation_id = None
        if S(case.state) != S.DISCOVERED:
            if S(case.state) == S.DESIGN_VALIDATING:
                move(session, case, S.DESIGN_IN_PROGRESS)
            elif S(case.state) != S.DESIGN_IN_PROGRESS:
                move(session, case, S.DESIGN_IN_PROGRESS)
        audit(
            session, key, "design.requirements.registered", "orchestrator", {"scope_id": identity}
        )
    return identity


def latest_decision(session: Session, case_id: str, subject: str, kind: str):
    return session.scalar(
        select(DesignDecision)
        .where(
            DesignDecision.case_id == case_id,
            DesignDecision.subject == subject,
            DesignDecision.kind == kind,
        )
        .order_by(DesignDecision.created_at.desc(), DesignDecision.id.desc())
    )


def require_approval(session: Session, case: DesignCase, subject: str, kind: str):
    from .config.settings import Settings

    decision = latest_decision(session, case.id, subject, kind)
    if decision is None or decision.decision != "approved":
        raise PermissionError(f"Authorized human {kind} approval is required")
    if decision.actor not in Settings().design_approvers:
        raise PermissionError("Previously authenticated approver is no longer authorized")
    return decision


def artifacts_of(revision: DesignRevision) -> list[Artifact]:
    return [Artifact.model_validate(a) for a in revision.payload["artifacts"]]


def export_revision(engine: Engine, revision_id: str):
    with Session(engine) as session:
        revision = session.get(DesignRevision, revision_id)
        if revision is None:
            raise ValueError("Unknown design revision")
        from .design_validation import expected_owners

        inputs = DesignInput.model_validate(revision.payload["input"])
        artifacts = artifacts_of(revision)
        if any(a.repository not in expected_owners(a.type, inputs) for a in artifacts):
            raise ValueError("Artifact ownership violates documentation repository policy")
        write_artifacts(artifacts, revision.payload["repositories"])


def generate_design(
    engine: Engine,
    key: str,
    agents: DocumentationAgents,
    renderer: DiagramRenderer,
    tool_version: str,
    as_built: AsBuiltInput | None = None,
) -> str:
    with Session(engine) as session:
        case = session.get(DesignCase, key)
        if case is None or case.scope_id is None:
            raise ValueError(
                "Missing requirements; register verified requirements and obtain human approval first"
            )
        require_approval(session, case, case.scope_id, "requirements")
        scope = session.get(DesignScope, case.scope_id)
        inputs = DesignInput.model_validate(scope.payload["input"])
        repositories = scope.payload["repositories"]
        phase = "as-built" if as_built else "design"
        if as_built:
            if S(case.state) not in {S.IMPLEMENTATION_VALIDATING, S.AWAITING_DELIVERY_APPROVAL}:
                raise ValueError("As-built reconciliation requires completed implementation tasks")
            inputs = inputs.model_copy(
                update={
                    "narratives": as_built.narratives,
                    "context": as_built.context,
                    "diagrams": as_built.diagrams,
                    "contracts": as_built.contracts,
                }
            )
            inputs = DesignInput.model_validate(inputs.model_dump())
        elif S(case.state) in {
            S.IMPLEMENTING,
            S.IMPLEMENTATION_VALIDATING,
            S.AWAITING_DELIVERY_APPROVAL,
            S.COMPLETED,
        }:
            raise ValueError("Design generation cannot replace an active implementation design")
        identity = digest(
            canonical(
                {
                    "scope_id": case.scope_id,
                    "phase": phase,
                    "input": inputs.model_dump(mode="json"),
                    "agent_version": agents.version,
                    "tool_version": tool_version,
                }
            )
        )
        existing = session.get(DesignRevision, identity)
        if existing is not None:
            # Rejected versions require changed input; regeneration cannot erase a rejection.
            if case.revision_id != identity:
                raise ValueError("A previous revision cannot silently replace the active revision")
            from .design_validation import expected_owners

            if any(
                a.repository not in expected_owners(a.type, inputs) for a in artifacts_of(existing)
            ):
                raise ValueError("Artifact ownership violates documentation repository policy")
            write_artifacts(artifacts_of(existing), existing.payload["repositories"])
            return identity
        if not as_built and S(case.state) in {
            S.AWAITING_DESIGN_APPROVAL,
            S.DESIGN_APPROVED,
            S.IMPLEMENTATION_READY,
        }:
            # A changed generator/tool version requires a new design and approval.
            pass
        scope_id = case.scope_id
    from .design_validation import verify_stored_context

    verify_stored_context(inputs, repositories)
    with Session(engine) as session, session.begin():
        case = session.get(DesignCase, key)
        if phase == "design" and S(case.state) != S.DESIGN_IN_PROGRESS:
            move(session, case, S.DESIGN_IN_PROGRESS)
        audit(
            session,
            key,
            "design.generation.started",
            "orchestrator",
            {"phase": phase, "scope_id": scope_id},
        )
    outputs, findings, tasks = [], [], []
    for role in ROLES if phase == "design" else ("solution-architect", "technical-writer"):
        task = DocumentationTask(
            role=role, phase=phase, milestone=inputs.plan.id, scope_digest=scope_id
        )
        try:
            result = agents.generate(task, inputs)
        except Exception as exc:
            with Session(engine) as session, session.begin():
                audit(
                    session,
                    key,
                    "design.documentation-task.failed",
                    "orchestrator",
                    {"role": role, "phase": phase, "error_type": type(exc).__name__},
                )
            raise
        outputs.extend(result.artifacts)
        findings.extend(result.findings)
        tasks.append({**task.model_dump(), "state": "succeeded", "adapter": agents.version})
    generated_at = now()
    prefix = f"docs/milestones/{inputs.plan.id}/revisions/{identity}"
    rendered = []
    for artifact in outputs:
        artifact = artifact.model_copy(deep=True)
        artifact.path = prefix + "/" + artifact.path
        artifact.generated_at = generated_at
        if artifact.type.startswith("diagram:"):
            svg, problems = renderer.render(artifact.content)
            findings.extend(problems)
            if svg is not None:
                rendered.append(
                    Artifact(
                        type=artifact.type.replace("diagram:", "render:"),
                        repository=artifact.repository,
                        path=artifact.path.removesuffix(".puml") + ".svg",
                        content=svg,
                        sha256=digest(svg),
                        requirement_ids=artifact.requirement_ids,
                        agent=artifact.agent,
                        generated_at=generated_at,
                    )
                )
        rendered.append(artifact)
    links = "\n## Related artifacts\n\n" + "\n".join(
        f"- [Directory entry](aeo://{a.repository}/{a.path})" for a in rendered
    )
    for artifact in rendered:
        if artifact.path.endswith(".md"):
            artifact.content += links + "\n"
            artifact.sha256 = digest(artifact.content)
    # Persist first: interrupted publication can be repaired from the immutable DB payload.
    payload = {
        "input": inputs.model_dump(mode="json"),
        "repositories": repositories,
        "artifacts": [a.model_dump(mode="json") for a in rendered],
        "generation_findings": [f.model_dump() for f in findings],
        "documentation_tasks": tasks,
        "agent_version": agents.version,
        "tool_version": tool_version,
    }
    payload["bundle_digest"] = digest(
        canonical(
            {
                "scope_id": scope_id,
                "artifacts": [
                    {
                        k: a[k]
                        for k in (
                            "type",
                            "repository",
                            "path",
                            "sha256",
                            "requirement_ids",
                            "agent",
                        )
                    }
                    for a in payload["artifacts"]
                ],
            }
        )
    )
    with Session(engine) as session, session.begin():
        case = session.get(DesignCase, key)
        if case.scope_id != scope_id:
            raise ValueError("Scope changed during generation")
        if phase == "design":
            if S(case.state) != S.DESIGN_IN_PROGRESS:
                move(session, case, S.DESIGN_IN_PROGRESS)
        elif S(case.state) == S.AWAITING_DELIVERY_APPROVAL:
            move(session, case, S.IMPLEMENTATION_VALIDATING)
        session.add(
            DesignRevision(
                id=identity, case_id=key, scope_id=scope_id, phase=phase, payload=payload
            )
        )
        case.revision_id = identity
        case.validation_id = None
        audit(
            session,
            key,
            "design.generated",
            "orchestrator",
            {"revision_id": identity, "phase": phase, "tasks": tasks},
        )
    export_revision(engine, identity)
    return identity


def validate_design(engine: Engine, key: str, reviewer: ArchitectureReviewer) -> dict:
    with Session(engine) as session:
        case = session.get(DesignCase, key)
        if case is None or not case.revision_id:
            raise ValueError(
                "No design artifacts; approved requirements and generation are required"
            )
        revision = session.get(DesignRevision, case.revision_id)
        require_approval(session, case, revision.scope_id, "requirements")
        inputs = DesignInput.model_validate(revision.payload["input"])
        artifacts = artifacts_of(revision)
        findings = [Finding.model_validate(f) for f in revision.payload["generation_findings"]]
        if S(case.state) not in {S.IMPLEMENTING, S.COMPLETED}:
            from .design_validation import verify_stored_context

            try:
                verify_stored_context(inputs, revision.payload["repositories"])
            except (OSError, ValueError) as exc:
                findings.append(Finding(code="stale-context", message=str(exc)))
        findings += deterministic_findings(
            inputs,
            artifacts,
            revision.payload["repositories"],
            revision.phase,
            revision.scope_id,
            revision.id,
        )
        try:
            review_findings = reviewer.review(inputs, artifacts)
            review_state = "succeeded"
        except Exception as exc:
            review_state = "failed"
            review_findings = [
                Finding(code="architecture-review-failed", message=type(exc).__name__)
            ]
        findings.extend(review_findings)
        payload = {
            "passed": not any(f.severity == "error" for f in findings),
            "findings": [f.model_dump() for f in findings],
            "review_task": {
                "role": "solution-architect",
                "task": "independent-architecture-review",
                "adapter": reviewer.version,
                "state": review_state,
            },
        }
        identity = digest(revision.id + canonical(payload))
        revision_id, phase = revision.id, revision.phase
    with Session(engine) as session, session.begin():
        case = session.get(DesignCase, key)
        if case.revision_id != revision_id:
            raise ValueError("Revision changed during validation")
        if case.validation_id != identity:
            case.validation_id = identity
            audit(
                session,
                key,
                "design.validation.selected",
                "orchestrator",
                {"validation_id": identity},
            )
        if session.get(DesignValidation, identity) is None:
            session.add(DesignValidation(id=identity, revision_id=revision_id, payload=payload))
            audit(
                session,
                key,
                "design.validated",
                "orchestrator",
                {"revision_id": revision_id, "validation_id": identity, **payload},
            )
        if phase == "design" and S(case.state) in {S.DESIGN_IN_PROGRESS, S.DESIGN_VALIDATING}:
            if S(case.state) == S.DESIGN_IN_PROGRESS:
                move(session, case, S.DESIGN_VALIDATING)
            move(
                session,
                case,
                S.AWAITING_DESIGN_APPROVAL if payload["passed"] else S.DESIGN_IN_PROGRESS,
            )
        elif (
            phase == "as-built"
            and S(case.state) == S.IMPLEMENTATION_VALIDATING
            and payload["passed"]
        ):
            move(session, case, S.AWAITING_DELIVERY_APPROVAL)
        elif not payload["passed"] and S(case.state) in {
            S.AWAITING_DESIGN_APPROVAL,
            S.DESIGN_APPROVED,
            S.IMPLEMENTATION_READY,
        }:
            move(session, case, S.DESIGN_IN_PROGRESS)
        elif not payload["passed"] and S(case.state) == S.AWAITING_DELIVERY_APPROVAL:
            move(session, case, S.IMPLEMENTATION_VALIDATING)
    return {"validation_id": identity, **payload}


def approval_subject(engine: Engine, key: str, kind: str) -> str:
    with Session(engine) as session:
        case = session.get(DesignCase, key)
        if case is None:
            raise ValueError("No milestone requirements registered")
        if kind == "requirements":
            return case.scope_id
        revision = session.get(DesignRevision, case.revision_id) if case.revision_id else None
        if revision is None:
            raise ValueError("No artifact revision")
        return revision.payload["bundle_digest"]


def decide(
    engine: Engine,
    key: str,
    kind: str,
    approved: bool,
    verifier: HumanVerifier,
    approvers: list[str],
) -> str:
    if kind not in {"requirements", "design", "delivery"}:
        raise ValueError("Unknown human decision kind")
    if not approvers:
        raise PermissionError(
            "No authenticated design approvers configured; set AEO_DESIGN_APPROVERS to authorized Windows SID identities"
        )
    subject = approval_subject(engine, key, kind)
    decision_text = "approved" if approved else "rejected"
    actor = verifier.verify(key + ":" + kind + ":" + subject, decision_text)
    if actor not in approvers:
        raise PermissionError("Authenticated human is not an authorized design approver")
    with Session(engine) as session, session.begin():
        case = session.get(DesignCase, key)
        revision = session.get(DesignRevision, case.revision_id) if case.revision_id else None
        current_subject = (
            case.scope_id if kind == "requirements" else revision.payload["bundle_digest"]
        )
        if subject != current_subject:
            raise ValueError("Approval subject changed during authentication")
        if kind == "requirements":
            if S(case.state) not in {S.DISCOVERED, S.DESIGN_IN_PROGRESS}:
                raise ValueError("Requirements decision requires a revision workflow")
        else:
            expected_state = (
                S.AWAITING_DESIGN_APPROVAL if kind == "design" else S.AWAITING_DELIVERY_APPROVAL
            )
            if S(case.state) != expected_state:
                raise ValueError("Artifacts must pass validation before human review")
            if (kind == "design") != (revision.phase == "design"):
                raise ValueError("Wrong artifact phase for approval")
            from .design_validation import verify_stored_context

            verify_stored_context(
                DesignInput.model_validate(revision.payload["input"]),
                revision.payload["repositories"],
            )
            problems = check_files(artifacts_of(revision), revision.payload["repositories"])
            if problems:
                raise PermissionError(
                    "Artifacts changed or are missing; revise and revalidate before approval"
                )
            validation = (
                session.get(DesignValidation, case.validation_id) if case.validation_id else None
            )
            if validation is None or not validation.payload["passed"]:
                raise PermissionError("Deterministic validation and independent review must pass")
            require_approval(session, case, revision.scope_id, "requirements")
        identity = str(uuid4())
        session.add(
            DesignDecision(
                id=identity,
                case_id=key,
                subject=subject,
                kind=kind,
                decision=decision_text,
                actor=actor,
                payload={
                    "scope_id": case.scope_id,
                    "revision_id": revision.id if revision and kind != "requirements" else None,
                    "validation_id": validation.id if kind != "requirements" else None,
                },
            )
        )
        if kind == "design":
            move(session, case, S.DESIGN_APPROVED if approved else S.DESIGN_IN_PROGRESS, actor)
        elif kind == "delivery":
            if approved:
                from .config.settings import Settings
                from .quality import assert_delivery

                milestone = session.scalar(
                    select(Milestone).where(
                        Milestone.project_id == case.project_id,
                        Milestone.external_id == case.external_id,
                    )
                )
                if milestone is not None:
                    assert_delivery(session, Settings(), milestone, consume=True)
            move(session, case, S.COMPLETED if approved else S.IMPLEMENTATION_VALIDATING, actor)
        audit(
            session,
            key,
            "design.human-decision",
            actor,
            {"decision_id": identity, "kind": kind, "subject": subject, "decision": decision_text},
        )
    return identity


def assert_design_gate(session: Session, milestone: Milestone) -> DesignCase:
    key = case_key(milestone.project_id, milestone.external_id)
    case = session.get(DesignCase, key)
    if case is None or S(case.state) not in {S.IMPLEMENTATION_READY, S.IMPLEMENTING}:
        raise PermissionError("Implementation requires an approved design in IMPLEMENTATION_READY")
    revision = session.get(DesignRevision, case.revision_id)
    if revision is None or revision.phase != "design":
        raise PermissionError("Approved design revision is missing")
    require_approval(session, case, revision.scope_id, "requirements")
    require_approval(session, case, revision.payload["bundle_digest"], "design")
    if S(case.state) == S.IMPLEMENTATION_READY:
        from .design_validation import verify_stored_context

        try:
            verify_stored_context(
                DesignInput.model_validate(revision.payload["input"]),
                revision.payload["repositories"],
            )
        except (OSError, ValueError) as exc:
            raise PermissionError(
                "Approved repository context changed; revise the design before implementation"
            ) from exc
    if revision.payload["input"]["plan"] != milestone.spec:
        raise PermissionError("Implementation plan differs from approved design scope")
    validation = session.get(DesignValidation, case.validation_id) if case.validation_id else None
    if validation is None or not validation.payload["passed"]:
        raise PermissionError("Design validation/review is missing or failed")
    if check_files(artifacts_of(revision), revision.payload["repositories"]):
        raise PermissionError(
            "Approved design artifacts changed; new revision and human review required"
        )
    return case


def implementation_ready(engine: Engine, key: str):
    with Session(engine) as session, session.begin():
        case = session.get(DesignCase, key)
        if case is None or S(case.state) != S.DESIGN_APPROVED:
            raise PermissionError("Human design approval required")
        # Temporarily enter ready inside the transaction so the same guard checks exact scope/files.
        move(session, case, S.IMPLEMENTATION_READY)
        milestone = session.scalar(
            select(Milestone).where(
                Milestone.project_id == case.project_id, Milestone.external_id == case.external_id
            )
        )
        if milestone is None:
            raise ValueError(
                "Approved plan must be imported through the existing plan service first"
            )
        assert_design_gate(session, milestone)


def implementation_complete(engine: Engine, key: str):
    with Session(engine) as session, session.begin():
        case = session.get(DesignCase, key)
        if case is None or S(case.state) != S.IMPLEMENTING:
            raise ValueError("Milestone is not implementing")
        milestone = session.scalar(
            select(Milestone).where(
                Milestone.project_id == case.project_id, Milestone.external_id == case.external_id
            )
        )
        tasks = list(session.scalars(select(Task).where(Task.milestone_id == milestone.id)))
        if not tasks or any(t.state != "succeeded" for t in tasks):
            raise ValueError("All implementation tasks must succeed before as-built reconciliation")
        move(session, case, S.IMPLEMENTATION_VALIDATING)


def design_status(engine: Engine, key: str) -> dict:
    with Session(engine) as session:
        case = session.get(DesignCase, key)
        if case is None:
            return {
                "milestone": key,
                "state": S.DISCOVERED.value,
                "findings": [
                    {
                        "code": "missing-requirements",
                        "message": "No approved requirements; implementation is blocked",
                    }
                ],
            }
        scope = session.get(DesignScope, case.scope_id)
        revision = session.get(DesignRevision, case.revision_id) if case.revision_id else None
        decisions = list(
            session.scalars(
                select(DesignDecision)
                .where(DesignDecision.case_id == key)
                .order_by(DesignDecision.created_at, DesignDecision.id)
            )
        )
        validation = (
            session.get(DesignValidation, case.validation_id) if case.validation_id else None
        )
        approved = (
            latest_decision(
                session,
                key,
                revision.payload["bundle_digest"],
                "design" if revision.phase == "design" else "delivery",
            )
            if revision
            else None
        )
        inputs = DesignInput.model_validate(
            (revision.payload if revision else scope.payload)["input"]
        )
        artifacts = []
        if revision:
            for artifact in artifacts_of(revision):
                artifacts.append(
                    {
                        **artifact.model_dump(exclude={"content"}),
                        "source_requirements": artifact.requirement_ids,
                        "validation_status": "passed"
                        if validation and validation.payload["passed"]
                        else "pending-or-failed",
                        "approval_status": approved.decision if approved else "pending",
                        "approved_version": revision.id
                        if approved and approved.decision == "approved"
                        else None,
                        "absolute_path": str(
                            Path(revision.payload["repositories"][artifact.repository])
                            / artifact.path
                        ),
                    }
                )
        authorized = False
        authorization_findings = []
        if S(case.state) in {S.IMPLEMENTATION_READY, S.IMPLEMENTING}:
            milestone = session.scalar(
                select(Milestone).where(
                    Milestone.project_id == case.project_id,
                    Milestone.external_id == case.external_id,
                )
            )
            try:
                if milestone is None:
                    raise PermissionError("Approved implementation plan has not been imported")
                assert_design_gate(session, milestone)
                authorized = True
            except (PermissionError, ValueError, OSError) as exc:
                authorization_findings.append(str(exc))
        history = [
            {
                "revision_id": r.id,
                "phase": r.phase,
                "scope_id": r.scope_id,
                "bundle_digest": r.payload["bundle_digest"],
                "created_at": r.created_at,
            }
            for r in session.scalars(
                select(DesignRevision)
                .where(DesignRevision.case_id == key)
                .order_by(DesignRevision.created_at, DesignRevision.id)
            )
        ]
        return {
            "milestone": key,
            "state": case.state,
            "scope_id": case.scope_id,
            "revision_id": case.revision_id,
            "summary": inputs.plan.title,
            "functional_scope": [r.model_dump() for r in inputs.requirements],
            "architecture_overview": inputs.narratives.get("architecture", {}),
            "technical_decisions": inputs.narratives.get("architecture", {}).get(
                "Technology decisions", "MISSING"
            ),
            "risks_and_assumptions": inputs.narratives.get("architecture", {}).get(
                "Risks and assumptions", "MISSING"
            ),
            "affected_repositories": sorted(scope.payload["repositories"]),
            "verified_context": [c.model_dump() for c in inputs.context],
            "implementation_tasks": [t.model_dump(mode="json") for t in inputs.plan.tasks],
            "artifacts": artifacts,
            "validation": validation.payload if validation else None,
            "file_findings": [
                f.model_dump()
                for f in check_files(artifacts_of(revision), revision.payload["repositories"])
            ]
            if revision
            else [],
            "decisions": [
                {
                    "kind": d.kind,
                    "subject": d.subject,
                    "decision": d.decision,
                    "actor": d.actor,
                    "created_at": d.created_at,
                }
                for d in decisions
            ],
            "implementation_authorized": authorized,
            "authorization_findings": authorization_findings,
            "revision_history": history,
        }


def observe_documentation_bundle(engine: Engine, root: Path, manifest: dict) -> str:
    """Archive references to manually produced framework documentation; grants no approval.

    Reuses the artifact contract and append-only audit, without importing an application plan
    or creating a synthetic authenticated design decision.
    """
    from .design_artifacts import owned_path
    from .persistence import AuditEvent

    identity = "documentation-bundle:" + manifest["revision_id"]
    for item in manifest["artifacts"]:
        path = owned_path(root, item["relative_file_path"])
        content = path.read_bytes().decode("utf-8")
        artifact = Artifact(
            type=item["artifact_type"],
            repository=item["owning_repository"],
            path=item["relative_file_path"],
            content=content,
            sha256=item["content_hash"],
            requirement_ids=item["source_requirements"],
            agent=item["generating_agent"],
            generated_at=item["generated_timestamp"],
        )
        if artifact.sha256 != digest(content) or artifact.repository != "agrosphere-orchestrator":
            raise ValueError("Documentation bundle artifact integrity/ownership mismatch")
    with Session(engine) as session, session.begin():
        previous = session.scalar(
            select(AuditEvent).where(
                AuditEvent.entity_id == identity, AuditEvent.kind == "documentation.bundle.observed"
            )
        )
        if previous is not None:
            if canonical(previous.payload) != canonical(manifest):
                raise ValueError("Observed documentation revision has different manifest content")
            return identity
        audit(session, identity, "documentation.bundle.observed", "orchestrator", manifest)
    return identity
