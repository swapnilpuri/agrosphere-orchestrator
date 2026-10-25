"""Independent delivery governance, sharing AEO persistence, approval and repair boundaries."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select

from .configuration import RepositoryManifest, load_yaml
from .design import artifacts_of, check_files, require_approval
from .design_models import case_key
from .execution_models import ExecutionPolicy
from .execution_workspace import git, tree_fingerprints
from .orchestration import milestone_record
from .orchestration_store import evidence, transaction
from .persistence import (
    DesignCase,
    DesignDecision,
    DesignRevision,
    DesignScope,
    Execution,
    Task,
    now,
)
from .quality_adapters import SandboxedValidator, architecture, documentation, interpret
from .quality_models import ApprovalCategory, Finding, GateResult, GateState, QualityPolicy
from .quality_store import GovernanceRecord, blob, digest, read_blob, record


def history(session, milestone, kind):
    return list(
        session.scalars(
            select(GovernanceRecord)
            .where(GovernanceRecord.milestone_id == milestone, GovernanceRecord.kind == kind)
            .order_by(GovernanceRecord.sequence)
        )
    )


def tasks_for(session, milestone):
    return list(
        session.scalars(
            select(Task).where(Task.milestone_id == milestone.id).order_by(Task.external_id)
        )
    )


def design_context(session, milestone):
    case = session.get(DesignCase, case_key(milestone.project_id, milestone.external_id))
    if case is None or not case.scope_id:
        raise PermissionError("Approved requirement scope is missing")
    if case.state in {
        "DISCOVERED",
        "DESIGN_IN_PROGRESS",
        "DESIGN_VALIDATING",
        "AWAITING_DESIGN_APPROVAL",
    }:
        raise PermissionError("Architecture revision is pending human approval")
    scope = session.get(DesignScope, case.scope_id)
    require_approval(session, case, case.scope_id, "requirements")
    decisions = list(
        session.scalars(
            select(DesignDecision)
            .where(DesignDecision.case_id == case.id, DesignDecision.kind == "design")
            .order_by(DesignDecision.created_at, DesignDecision.id)
        )
    )
    if not decisions or decisions[-1].decision != "approved":
        raise PermissionError("Approved architecture is missing")
    revision = session.get(DesignRevision, decisions[-1].payload.get("revision_id"))
    if (
        revision is None
        or revision.scope_id != case.scope_id
        or check_files(artifacts_of(revision), revision.payload["repositories"])
    ):
        raise PermissionError("Approved architecture artifacts changed; design revision required")
    require_approval(session, case, revision.payload["bundle_digest"], "design")
    current_revision = session.get(DesignRevision, case.revision_id) if case.revision_id else None
    if (
        current_revision
        and current_revision.phase == "design"
        and current_revision.id != revision.id
    ):
        raise PermissionError("Current design revision is not approved")
    return case, scope, revision


def repositories(settings):
    return {
        r.id: r
        for r in load_yaml(settings.repository_manifest, RepositoryManifest).resolve(
            settings.repository_manifest
        )
        if r.status == "confirmed"
    }


def snapshot(session, settings, milestone):
    repos = repositories(settings)
    roots = {}
    for task in tasks_for(session, milestone):
        repo = repos.get(task.spec["repository"])
        if repo is None:
            raise PermissionError("Unconfirmed repository")
        execution = session.scalar(
            select(Execution)
            .where(Execution.task_id == task.id, Execution.state == "SUCCEEDED")
            .order_by(Execution.created_at.desc(), Execution.id.desc())
        )
        root = repo.path
        if execution and execution.request["mode"] != "READ_ONLY":
            if not execution.result or not execution.result.get("implementation_verified"):
                raise PermissionError("Write lacks deterministic execution validation")
            root = Path(execution.request["worktree_path"])
        if (
            repo.id in roots
            and roots[repo.id] != repo.path
            and roots[repo.id] != root
            and root != repo.path
        ):
            raise PermissionError("Reconcile multiple write worktrees before milestone validation")
        if repo.id not in roots or root != repo.path:
            roots[repo.id] = root
    artifacts = {}
    for name, root in sorted(roots.items()):
        artifacts[name] = {
            "root": str(root.resolve()),
            "head": git(root, "rev-parse", "HEAD"),
            "tree": digest(tree_fingerprints(root, 100000000)),
        }
    return artifacts


def context(session, settings, milestone, policy):
    case, scope, revision = design_context(session, milestone)
    return {
        "project": milestone.project_id,
        "milestone": milestone.external_id,
        "scope": scope.id,
        "design": revision.id,
        "as_built": case.revision_id,
        "policy": digest(policy.model_dump(mode="json")),
        "repositories": snapshot(session, settings, milestone),
        "execution_policy": digest(
            load_yaml(settings.execution_policy, ExecutionPolicy).model_dump(mode="json")
        ),
        "repository_manifest": digest(
            load_yaml(settings.repository_manifest, RepositoryManifest).model_dump(mode="json")
        ),
    }


def check_policy_scope(policy, milestone, scope):
    tasks = {t["id"]: t for t in milestone.spec["tasks"]}
    requirements = {r["id"]: r for r in scope.payload["input"]["requirements"]}
    for gate in policy.gates:
        if gate.repository not in {t["repository"] for t in tasks.values()}:
            raise ValueError("Gate repository outside milestone")
        if gate.milestones and milestone.external_id not in gate.milestones:
            raise ValueError("Policy gate outside milestone scope")
        if any(t not in tasks or tasks[t]["repository"] != gate.repository for t in gate.tasks):
            raise ValueError("Gate task scope differs from repository ownership")
    for criterion in policy.criteria:
        requirement = requirements.get(criterion.requirement_id)
        if not requirement or criterion.task not in tasks:
            raise ValueError("Unknown approved requirement or implementing task")
        try:
            index = int(criterion.criterion_id.removeprefix("AC-"))
            if criterion.criterion_id != "AC-" + str(index) or not 1 <= index <= len(
                requirement["acceptance_criteria"]
            ):
                raise ValueError("Invalid criterion index")
            expected = requirement["acceptance_criteria"][index - 1]
        except (ValueError, IndexError):
            raise ValueError("Criterion ID must identify approved AC-1, AC-2, ...") from None
        if expected != criterion.criterion_text:
            raise ValueError("Criterion text differs from approved requirements")
        if not criterion.human:
            gate = next(g for g in policy.gates if g.id == criterion.gate)
            if (
                gate.repository != tasks[criterion.task]["repository"]
                or (gate.tasks and criterion.task not in gate.tasks)
                or not criterion.test_case
            ):
                raise ValueError("Criterion lacks task-scoped deterministic test mapping")


def activate_policy(engine, settings, external_id, verifier, project="agrosphere"):
    policy = load_yaml(settings.quality_policy, QualityPolicy)
    payload = policy.model_dump(mode="json")
    subject = digest(payload)
    actor = verifier.verify(
        "quality-policy:" + project + ":" + external_id + ":" + subject, "approved"
    )
    if actor not in settings.governance_approvers or not actor.startswith("sid:"):
        raise PermissionError("Authenticated actor is not a governance policy approver")
    with transaction(engine) as session:
        milestone = milestone_record(session, external_id, project)
        _, scope, _ = design_context(session, milestone)
        check_policy_scope(policy, milestone, scope)
        if load_yaml(settings.quality_policy, QualityPolicy) != policy:
            raise PermissionError("Policy changed during authentication")
        previous = history(session, milestone.id, "policy.activated")
        if previous:
            prior = QualityPolicy.model_validate(read_blob(session, previous[-1].payload["policy"]))
            if prior != policy and (prior.id != policy.id or policy.version <= prior.version):
                raise PermissionError("Policy revisions require a strictly increasing version")
        identity = blob(session, payload)
        record(
            session, milestone.id, "policy.activated", {"policy": identity, "actor": actor}, actor
        )
        return identity


def active_policy(session, settings, milestone):
    active = history(session, milestone.id, "policy.activated")
    if not active:
        raise PermissionError("No authenticated quality policy is active")
    if active[-1].payload["actor"] not in settings.governance_approvers:
        raise PermissionError("Policy approver no longer authorized")
    policy = QualityPolicy.model_validate(read_blob(session, active[-1].payload["policy"]))
    if load_yaml(settings.quality_policy, QualityPolicy) != policy:
        raise PermissionError(
            "Unauthorized policy change; activate a new human-reviewed policy version"
        )
    _, scope, _ = design_context(session, milestone)
    check_policy_scope(policy, milestone, scope)
    return policy


def quality_state(session, task, state, run):
    source = task.quality_state
    task.quality_state = state
    record(
        session,
        task.milestone_id,
        "task.state",
        {"from": source, "to": state, "validation": run},
        task=task.id,
    )


async def validate(engine, settings, external_id, project="agrosphere", validator=None):
    validator = validator or SandboxedValidator(settings)
    run = str(uuid4())
    with transaction(engine) as session:
        milestone = milestone_record(session, external_id, project)
        policy = active_policy(session, settings, milestone)
        bound = context(session, settings, milestone, policy)
        commands = {
            c.id: c
            for c in load_yaml(settings.execution_policy, ExecutionPolicy).validation_commands
        }
        tasks = tasks_for(session, milestone)
        if any(t.state != "succeeded" for t in tasks):
            raise PermissionError(
                "All implementing and review tasks must complete before validation"
            )
        for task in tasks:
            quality_state(session, task, "IMPLEMENTED", run)
            quality_state(session, task, "VALIDATING", run)
        record(session, milestone.id, "validation.started", {"run": run, "context": bound})
        milestone_id = milestone.id
    results = []
    for gate in policy.gates:
        started = now()
        result = GateResult(
            gate_id=gate.id,
            execution_id=run,
            repository=gate.repository,
            artifact_hash=digest(bound["repositories"][gate.repository]),
            validator_version=gate.validator_version,
            started_at=started,
            ended_at=started,
            state=GateState.RUNNING,
            policy_version=policy.version,
            details={"configuration": gate.configuration},
        )
        with transaction(engine) as session:
            record(
                session,
                milestone_id,
                "gate.state",
                {"run": run, "gate": gate.id, "state": "PENDING"},
            )
            record(
                session,
                milestone_id,
                "gate.state",
                {"run": run, "gate": gate.id, "state": "RUNNING"},
            )
        raw = {}
        try:
            root = Path(bound["repositories"][gate.repository]["root"])
            if gate.skip:
                result.state = GateState.SKIPPED
            elif gate.evaluator == "files":
                raw = documentation(gate, root)
            elif gate.evaluator == "architecture":
                raw = architecture(gate, root)
            else:
                command_id = repositories(settings)[gate.repository].validators.get(
                    gate.command, gate.command
                )
                command = commands.get(command_id)
                if command is None:
                    raise PermissionError("Required validator is not administrator allowlisted")
                result.command = command.argv
                if gate.evaluator == "execution":
                    with transaction(engine) as session:
                        raw = execution_validation(session, milestone_id, gate, bound, command)
                else:
                    raw = await validator.evaluate(gate, root, command)
                raw = {**raw, **interpret(gate, raw)}
            if raw:
                result.state = raw["state"]
                result.exit_code = raw.get("exit_code")
                result.findings = [Finding.model_validate(f) for f in raw.get("findings", [])]
                result.test_cases = raw.get("test_cases", {})
                result.coverage = raw.get("coverage")
        except (PermissionError, FileNotFoundError) as exc:
            result.state = GateState.BLOCKED
            raw = {**raw, "error": str(exc)}
        except Exception as exc:
            result.state = GateState.ERROR
            raw = {**raw, "error": str(exc)}
        result.ended_at = now()
        with transaction(engine) as session:
            from .execution_process import Redactor

            raw = json.loads(Redactor().clean(json.dumps(raw)))
            result.evidence = [
                blob(session, {"raw": raw, "context": bound, "gate": gate.model_dump(mode="json")})
            ]
            # Revalidate assignments and enums before storing results.
            result = GateResult.model_validate_json(Redactor().clean(result.model_dump_json()))
            result_id = blob(session, result.model_dump(mode="json"))
            record(session, milestone_id, "gate.result", {"run": run, "result": result_id})
            if gate.type in {"architecture", "contract"} and result.state != GateState.PASSED:
                record(
                    session,
                    milestone_id,
                    "architecture.review",
                    {"run": run, "gate": gate.id, "design_revision_required": True},
                )
            results.append(result_id)
    with transaction(engine) as session:
        milestone = milestone_record(session, external_id, project)
        if (
            active_policy(session, settings, milestone) != policy
            or context(session, settings, milestone, policy) != bound
        ):
            record(
                session,
                milestone.id,
                "validation.invalidated",
                {"run": run, "reason": "Artifacts or policy changed during validation"},
            )
        else:
            record(
                session,
                milestone.id,
                "validation.completed",
                {"run": run, "context": bound, "results": results, "ended_at": now()},
            )
            for repair in history(session, milestone.id, "remediation.prepared"):
                if repair.payload["validation"] == run:
                    continue
                if any(
                    r.payload.get("repair") == repair.id
                    for r in history(session, milestone.id, "remediation.revalidated")
                ):
                    continue
                current_execution = session.scalar(
                    select(Execution)
                    .where(Execution.task_id == repair.task_id)
                    .order_by(Execution.created_at.desc())
                )
                outcome = next(
                    (
                        read_blob(session, ref)
                        for ref in results
                        if read_blob(session, ref)["gate_id"] == repair.payload["gate"]
                    ),
                    None,
                )
                record(
                    session,
                    milestone.id,
                    "remediation.revalidated",
                    {
                        "repair": repair.id,
                        "run": run,
                        "new_evidence": results,
                        "agent_execution_id": current_execution.id if current_execution else None,
                        "files_changed": (current_execution.result or {}).get("changed_files", [])
                        if current_execution
                        else [],
                        "retry_count": repair.payload["retry_count"],
                        "final_result": outcome["state"] if outcome else "BLOCKED",
                    },
                    task=repair.task_id,
                )
            for task in tasks_for(session, milestone):
                quality_state(session, task, "QUALITY_REVIEW", run)
                quality_state(session, task, "SECURITY_REVIEW", run)
    report = readiness(engine, settings, external_id, project)
    if report["decision"] == "READY_FOR_APPROVAL":
        request_approval(
            engine,
            settings,
            external_id,
            "DELIVERY_APPROVAL",
            "delivery",
            "quality-engine",
            "Required human review of validation " + run,
            project=project,
        )
        report = readiness(engine, settings, external_id, project)
    return report


def decisions(session, request):
    return list(
        session.scalars(
            select(DesignDecision)
            .where(
                DesignDecision.subject == request.id,
                DesignDecision.kind == "governance." + request.payload["category"],
            )
            .order_by(DesignDecision.created_at, DesignDecision.id)
        )
    )


def valid_approval(session, settings, request, current, consume=False):
    if request.payload["context"] != current or datetime.fromisoformat(
        request.payload["expires_at"]
    ) <= datetime.now(UTC):
        raise PermissionError("Approval expired or artifacts/policy changed")
    decided = decisions(session, request)
    if (
        not decided
        or decided[-1].decision != "approved"
        or decided[-1].actor not in settings.governance_approvers
    ):
        raise PermissionError("Missing, rejected, revoked or unauthorized human approval")
    if decided[-1].actor == request.payload["requesting_agent"]:
        raise PermissionError("Agents cannot self-approve")
    consumed = history(session, request.milestone_id, "approval.consumed")
    if any(r.payload["approval"] == request.id for r in consumed):
        raise PermissionError("One-time authorization already consumed")
    if consume:
        record(
            session,
            request.milestone_id,
            "approval.consumed",
            {"approval": request.id},
            decided[-1].actor,
        )
    return decided[-1]


def evaluate(session, settings, milestone):
    blockers, failures, results, criteria, pending = [], [], [], [], []
    report = {
        "milestone": milestone.external_id,
        "summary": milestone.spec["title"],
        "approved_scope": None,
        "repository_revisions": {},
        "build_results": [],
        "test_results": [],
        "coverage_results": [],
        "security_findings": [],
        "architecture_compliance": [],
        "contract_compatibility": [],
        "documentation_validation": [],
        "exceptions_and_waivers": [],
        "pending_approvals": pending,
        "outstanding_blockers": blockers,
        "acceptance_criteria": criteria,
        "gate_results": results,
        "decision": "BLOCKED",
        "evidence": [],
    }
    try:
        policy = active_policy(session, settings, milestone)
        current = context(session, settings, milestone, policy)
        report.update(
            approved_scope=current["scope"],
            repository_revisions=current["repositories"],
            context=current,
        )
        completed = history(session, milestone.id, "validation.completed")
        started = history(session, milestone.id, "validation.started")
        if not completed or (
            started and started[-1].payload["run"] != completed[-1].payload["run"]
        ):
            raise PermissionError("Latest validation is missing, interrupted or incomplete")
        validation = completed[-1]
        if validation.payload["context"] != current:
            raise PermissionError("Artifact or design change invalidated evidence")
        if datetime.fromisoformat(validation.payload["ended_at"]) + timedelta(
            seconds=policy.evidence_ttl_seconds
        ) <= datetime.now(UTC):
            raise PermissionError("Validation evidence expired")
        report["validation"] = validation.id
        report["evidence"] = validation.payload["results"]
        by_gate = {}
        for identity in validation.payload["results"]:
            result = GateResult.model_validate(read_blob(session, identity))
            for ref in result.evidence:
                read_blob(session, ref)
            if (
                result.execution_id != validation.payload["run"]
                or result.policy_version != policy.version
                or result.repository not in current["repositories"]
                or result.artifact_hash != digest(current["repositories"][result.repository])
            ):
                raise PermissionError(
                    "Gate evidence belongs to a different run, policy or artifact"
                )
            by_gate[result.gate_id] = result
            results.append(result.model_dump(mode="json"))
        applicable = policy.gates
        for gate in applicable:
            item = by_gate.get(gate.id)
            if item is None or not item.evidence:
                blockers.append("Missing evidence: " + gate.id)
                continue
            if item.state in {
                GateState.ERROR,
                GateState.BLOCKED,
                GateState.RUNNING,
                GateState.PENDING,
            }:
                if gate.blocking:
                    blockers.append("Validator unavailable or invalid: " + gate.id)
            elif item.state == GateState.SKIPPED:
                if not gate.allow_skip:
                    blockers.append("Unauthorized skip: " + gate.id)
            elif item.state != GateState.PASSED and gate.blocking:
                failures.append("Failed gate: " + gate.id)
            fields = {
                "build": "build_results",
                "test": "test_results",
                "coverage": "coverage_results",
                "architecture": "architecture_compliance",
                "contract": "contract_compatibility",
                "documentation": "documentation_validation",
            }
            if gate.type in fields:
                report[fields[gate.type]].append(item.model_dump(mode="json"))
            for finding in item.findings:
                entry = {**finding.model_dump(mode="json"), "gate": gate.id}
                if gate.type == "security":
                    report["security_findings"].append(entry)
                    if finding.severity in {"CRITICAL", "HIGH"} or (
                        finding.severity == "MEDIUM" and policy.medium_security_blocks
                    ):
                        waived = False
                        for waiver in history(session, milestone.id, "approval.request"):
                            if (
                                waiver.payload["category"]
                                not in {"SECURITY_EXCEPTION", "DEPENDENCY_EXCEPTION"}
                                or waiver.payload["action"] != gate.id + ":" + finding.id
                            ):
                                continue
                            if waiver.payload.get("finding_hash") != digest(entry):
                                continue
                            try:
                                decision = valid_approval(session, settings, waiver, current)
                                report["exceptions_and_waivers"].append(
                                    {
                                        "approval": waiver.id,
                                        "justification": decision.payload["justification"],
                                        "approver": decision.actor,
                                        "scope": waiver.payload["action"],
                                        "expires_at": waiver.payload["expires_at"],
                                    }
                                )
                                waived = True
                            except PermissionError:
                                pass
                        if not waived:
                            failures.append(
                                "Unwaived security finding: " + gate.id + ":" + finding.id
                            )
                elif gate.blocking and finding.severity in {"CRITICAL", "HIGH"}:
                    failures.append("Blocking finding: " + gate.id + ":" + finding.id)
        tasks = tasks_for(session, milestone)
        for repo in current["repositories"]:
            kinds = {
                g.type for g in applicable if g.repository == repo and g.blocking and not g.skip
            }
            missing = set(policy.required_gate_types) - kinds
            if missing:
                blockers.append(
                    "Required gate types absent for " + repo + ": " + ", ".join(sorted(missing))
                )
        if any(t.state != "succeeded" for t in tasks):
            blockers.append("Implementation/review task incomplete")
        for role in policy.required_review_roles:
            reviews = [t for t in tasks if t.spec["role"] == role]
            if not reviews or any(t.state != "succeeded" for t in reviews):
                blockers.append("Missing independent review role: " + role)
            for task in reviews:
                execution = session.scalar(
                    select(Execution)
                    .where(Execution.task_id == task.id, Execution.state == "SUCCEEDED")
                    .order_by(Execution.created_at.desc())
                )
                if execution is None or execution.request["mode"] != "READ_ONLY":
                    blockers.append(
                        "Review must use an independent read-only execution: " + task.external_id
                    )
        _, scope, _ = design_context(session, milestone)
        mappings = {(c.requirement_id, c.criterion_id): c for c in policy.criteria}
        for requirement in scope.payload["input"]["requirements"]:
            for index, text in enumerate(requirement["acceptance_criteria"], 1):
                key = (requirement["id"], "AC-" + str(index))
                mapping = mappings.get(key)
                status, refs = "NOT_EVALUATED", []
                if mapping and mapping.human:
                    status = "HUMAN_VERIFICATION_REQUIRED"
                    for req in history(session, milestone.id, "approval.request"):
                        if (
                            req.payload["action"] == "criterion:" + ":".join(key)
                            and req.payload["category"] == "DELIVERY_APPROVAL"
                        ):
                            try:
                                valid_approval(session, settings, req, current)
                                status, refs = "VERIFIED", [req.id]
                            except PermissionError:
                                pass
                elif mapping and mapping.gate in by_gate:
                    item = by_gate[mapping.gate]
                    outcome = item.test_cases.get(mapping.test_case)
                    status = (
                        "VERIFIED"
                        if outcome == "passed" and item.state == GateState.PASSED
                        else "FAILED"
                        if outcome == "failed"
                        else "NOT_EVALUATED"
                    )
                    refs = item.evidence
                criteria.append(
                    {
                        "requirement_id": key[0],
                        "criterion_id": key[1],
                        "text": text,
                        "task": mapping.task if mapping else None,
                        "test_case": mapping.test_case if mapping else None,
                        "result": status,
                        "evidence": refs,
                    }
                )
                if status != "VERIFIED":
                    blockers.append("Acceptance criterion " + ":".join(key) + ": " + status)
        blockers.extend(failures)
        report["decision"] = (
            "BLOCKED"
            if blockers and not failures
            else "NOT_READY"
            if blockers
            else "READY_FOR_APPROVAL"
        )
        delivery = [
            r
            for r in history(session, milestone.id, "approval.request")
            if r.payload["category"] == "DELIVERY_APPROVAL" and r.payload["action"] == "delivery"
        ]
        if not blockers:
            if delivery:
                latest = delivery[-1]
                try:
                    valid_approval(session, settings, latest, current)
                    report["decision"] = "APPROVED_FOR_DELIVERY"
                except PermissionError as exc:
                    pending.append({"approval": latest.id, "reason": str(exc)})
                    prior = decisions(session, latest)
                    if prior and prior[-1].decision in {"rejected", "revoked"}:
                        report["decision"] = "BLOCKED"
                        blockers.append("Delivery approval " + prior[-1].decision)
            else:
                pending.append(
                    {"category": "DELIVERY_APPROVAL", "reason": "Human decision required"}
                )
        return report
    except (PermissionError, ValueError, OSError, KeyError) as exc:
        blockers.append(str(exc))
        return report


def readiness(engine, settings, external_id, project="agrosphere", persist=True):
    with transaction(engine) as session:
        milestone = milestone_record(session, external_id, project)
        report = evaluate(session, settings, milestone)
        if persist:
            identity = blob(session, report)
            record(
                session,
                milestone.id,
                "readiness",
                {"report": identity, "decision": report["decision"]},
            )
            for task in tasks_for(session, milestone):
                if report["decision"] in {"READY_FOR_APPROVAL", "APPROVED_FOR_DELIVERY"}:
                    if task.quality_state != "DELIVERY_APPROVED":
                        quality_state(
                            session, task, "READY_FOR_DELIVERY_REVIEW", report.get("validation")
                        )
                        quality_state(
                            session, task, "AWAITING_DELIVERY_APPROVAL", report.get("validation")
                        )
                    if report["decision"] == "APPROVED_FOR_DELIVERY":
                        quality_state(session, task, "DELIVERY_APPROVED", report.get("validation"))
                elif task.quality_state in {
                    "DELIVERY_APPROVED",
                    "AWAITING_DELIVERY_APPROVAL",
                    "READY_FOR_DELIVERY_REVIEW",
                }:
                    quality_state(session, task, "VALIDATING", report.get("validation"))
            report["report_hash"] = identity
        return report


def request_approval(
    engine,
    settings,
    external_id,
    category,
    action,
    requesting_agent,
    justification,
    expires_seconds=900,
    project="agrosphere",
):
    category = ApprovalCategory(category)
    if not justification.strip() or not 1 <= expires_seconds <= 86400:
        raise ValueError("Justification and bounded expiration required")
    if (
        category == ApprovalCategory.DELIVERY_APPROVAL
        and action != "delivery"
        and not action.startswith("criterion:")
    ):
        raise ValueError("Unknown delivery approval action")
    with transaction(engine) as session:
        milestone = milestone_record(session, external_id, project)
        policy = active_policy(session, settings, milestone)
        current = context(session, settings, milestone, policy)
        if category == ApprovalCategory.DELIVERY_APPROVAL and action == "delivery":
            report = evaluate(session, settings, milestone)
            if report["decision"] not in {"READY_FOR_APPROVAL", "APPROVED_FOR_DELIVERY"}:
                raise PermissionError(
                    "Delivery cannot request approval before all quality gates pass"
                )
        finding_hash = None
        if category in {ApprovalCategory.SECURITY_EXCEPTION, ApprovalCategory.DEPENDENCY_EXCEPTION}:
            security_report = evaluate(session, settings, milestone)
            target = next(
                (
                    f
                    for f in security_report["security_findings"]
                    if action == f["gate"] + ":" + f["id"]
                ),
                None,
            )
            if target is None:
                raise PermissionError(
                    "Exception requires an existing deterministic scanner finding"
                )
            finding_hash = digest(target)
        for prior in history(session, milestone.id, "approval.request"):
            if (
                prior.payload["category"] == category.value
                and prior.payload["action"] == action
                and prior.payload["context"] == current
                and prior.payload.get("finding_hash") == finding_hash
            ):
                decided = decisions(session, prior)
                if decided and decided[-1].decision in {"rejected", "revoked"}:
                    raise PermissionError(
                        "Rejected/revoked authorization requires revised artifacts or policy"
                    )
                if datetime.fromisoformat(prior.payload["expires_at"]) > datetime.now(UTC):
                    return prior.id
        return record(
            session,
            milestone.id,
            "approval.request",
            {
                "project": project,
                "milestone": external_id,
                "category": category.value,
                "action": action,
                "requesting_agent": requesting_agent,
                "justification": justification,
                "finding_hash": finding_hash,
                "context": current,
                "expires_at": (datetime.now(UTC) + timedelta(seconds=expires_seconds)).isoformat(),
            },
        )


def inspect_approval(engine, identity):
    with transaction(engine) as session:
        request = session.scalar(
            select(GovernanceRecord).where(
                GovernanceRecord.id == identity, GovernanceRecord.kind == "approval.request"
            )
        )
        if request is None:
            raise ValueError("Unknown approval request")
        return {
            "id": request.id,
            **request.payload,
            "decisions": [
                {
                    "id": d.id,
                    "actor": d.actor,
                    "decision": d.decision,
                    "timestamp": d.created_at,
                    **d.payload,
                }
                for d in decisions(session, request)
            ],
        }


def decide_approval(engine, settings, identity, verifier, decision, justification):
    if decision not in {"approved", "rejected", "revoked"} or not justification.strip():
        raise ValueError("Explicit decision and justification required")
    reviewed = inspect_approval(engine, identity)
    subject = digest({k: v for k, v in reviewed.items() if k != "decisions"})
    actor = verifier.verify(identity + ":" + subject, decision)
    if (
        actor not in settings.governance_approvers
        or actor == reviewed["requesting_agent"]
        or not actor.startswith("sid:")
    ):
        raise PermissionError(
            "Only an authorized verified human SID can decide; agents cannot self-approve"
        )
    with transaction(engine) as session:
        request = session.scalar(select(GovernanceRecord).where(GovernanceRecord.id == identity))
        milestone = milestone_record(
            session, request.payload["milestone"], request.payload["project"]
        )
        policy = active_policy(session, settings, milestone)
        current = context(session, settings, milestone, policy)
        if request.payload["context"] != current or datetime.fromisoformat(
            request.payload["expires_at"]
        ) <= datetime.now(UTC):
            raise PermissionError("Approval scope changed or request expired")
        prior = decisions(session, request)
        if prior and (decision != "revoked" or prior[-1].decision != "approved"):
            raise PermissionError("A final decision cannot be replayed or rejection bypassed")
        if decision == "revoked" and not prior:
            raise PermissionError("Only an approved decision can be revoked")
        if decision == "approved" and request.payload["action"] == "delivery":
            if evaluate(session, settings, milestone)["decision"] != "READY_FOR_APPROVAL":
                raise PermissionError("Quality evidence no longer permits approval")
        case, _, _ = design_context(session, milestone)
        identity = str(uuid4())
        session.add(
            DesignDecision(
                id=identity,
                case_id=case.id,
                subject=request.id,
                kind="governance." + request.payload["category"],
                decision=decision,
                actor=actor,
                payload={
                    "justification": justification,
                    "context": current,
                    "expires_at": request.payload["expires_at"],
                },
            )
        )
        record(
            session,
            milestone.id,
            "approval.decided",
            {"request": request.id, "decision_id": identity, "decision": decision},
            actor,
        )
        return identity


def consume_approval(engine, settings, identity, category, action):
    with transaction(engine) as session:
        request = session.scalar(
            select(GovernanceRecord).where(
                GovernanceRecord.id == identity, GovernanceRecord.kind == "approval.request"
            )
        )
        if (
            request is None
            or request.payload["category"] != ApprovalCategory(category).value
            or request.payload["action"] != action
        ):
            raise PermissionError("Authorization action/category scope mismatch")
        milestone = milestone_record(
            session, request.payload["milestone"], request.payload["project"]
        )
        current = context(session, settings, milestone, active_policy(session, settings, milestone))
        if category in {"SECURITY_EXCEPTION", "DEPENDENCY_EXCEPTION"}:
            security_report = evaluate(session, settings, milestone)
            finding = next(
                (
                    f
                    for f in security_report["security_findings"]
                    if action == f["gate"] + ":" + f["id"]
                ),
                None,
            )
            if finding is None or digest(finding) != request.payload.get("finding_hash"):
                raise PermissionError("Security exception finding changed or is unavailable")
        if (
            action == "delivery"
            and evaluate(session, settings, milestone)["decision"] != "APPROVED_FOR_DELIVERY"
        ):
            raise PermissionError("Delivery evidence no longer valid")
        valid_approval(session, settings, request, current, consume=True)


def markdown_report(report):
    lines = [
        "# Release readiness: " + report["milestone"],
        "",
        "Decision: **" + report["decision"] + "**",
        "",
    ]
    for key, value in report.items():
        if key not in {"milestone", "decision"}:
            lines.extend(
                [
                    "## " + key.replace("_", " ").title(),
                    "",
                    "\u0060\u0060\u0060json",
                    json.dumps(value, indent=2),
                    "\u0060\u0060\u0060",
                    "",
                ]
            )
    return "\n".join(lines).replace("\u0060", chr(96))


def prepare_remediation(engine, settings, external_id, project="agrosphere"):
    """Feed failed deterministic gates into AEO-3 repair accounting. Never grants write replay."""
    with transaction(engine) as session:
        milestone = milestone_record(session, external_id, project)
        policy = active_policy(session, settings, milestone)
        report = evaluate(session, settings, milestone)
        if report["decision"] in {"READY_FOR_APPROVAL", "APPROVED_FOR_DELIVERY"}:
            return []
        affected = []
        by_gate = {g.id: g for g in policy.gates}
        for item in report["gate_results"]:
            gate = by_gate[item["gate_id"]]
            if item["state"] != "FAILED" or not gate.retry_eligible or gate.type == "security":
                continue
            for task in tasks_for(session, milestone):
                if task.spec["repository"] != gate.repository or (
                    gate.tasks and task.external_id not in gate.tasks
                ):
                    continue
                if task.spec["role"] != "developer":
                    continue
                previous = [
                    r
                    for r in history(session, milestone.id, "remediation.prepared")
                    if r.task_id == task.id
                ]
                if len(previous) >= settings.scheduler_max_repairs or any(
                    r.payload["validation"] == report["validation"] for r in previous
                ):
                    continue
                task.state = "failed"
                quality_state(session, task, "IMPLEMENTED", report["validation"])
                original = session.scalar(
                    select(Execution)
                    .where(Execution.task_id == task.id)
                    .order_by(Execution.created_at.desc())
                )
                payload = {
                    "validation": report["validation"],
                    "gate": gate.id,
                    "original_failure": item,
                    "instructions": "Repair within approved scope; retain scanners and policy. Request a fresh write grant.",
                    "retry_count": len(previous) + 1,
                    "agent_execution_id": session.scalar(
                        select(Execution.id)
                        .where(Execution.task_id == task.id)
                        .order_by(Execution.created_at.desc())
                    ),
                    "files_changed": (original.result or {}).get("changed_files", [])
                    if original
                    else [],
                }
                record(session, milestone.id, "remediation.prepared", payload, task=task.id)
                evidence(
                    session,
                    milestone.id,
                    task.id,
                    "task.result",
                    {"failure": "CODE_VALIDATION_FAILURE", "quality_failure": payload},
                )
                affected.append(task.id)
        return affected


def assert_delivery(session, settings, milestone, consume=False):
    """Shared guard for legacy AEO-1C delivery once a milestone adopts AEO-4."""
    if not history(session, milestone.id, "policy.activated"):
        return
    report = evaluate(session, settings, milestone)
    if report["decision"] != "APPROVED_FOR_DELIVERY":
        raise PermissionError(
            "AEO-4 blocks delivery: "
            + "; ".join(report["outstanding_blockers"])
            + "; human delivery approval required"
        )
    requests = [
        r
        for r in history(session, milestone.id, "approval.request")
        if r.payload["category"] == "DELIVERY_APPROVAL" and r.payload["action"] == "delivery"
    ]
    valid_approval(session, settings, requests[-1], report["context"], consume=consume)


def execution_validation(session, milestone_id, gate, bound, command):
    """Consume objective AEO-2 output only when its final validated snapshot is unchanged."""
    executions = list(
        session.scalars(
            select(Execution)
            .join(Task)
            .where(Task.milestone_id == milestone_id, Execution.state == "SUCCEEDED")
            .order_by(Execution.created_at.desc())
        )
    )
    for execution in executions:
        task = session.get(Task, execution.task_id)
        if task.spec["repository"] != gate.repository or (
            gate.tasks and task.external_id not in gate.tasks
        ):
            continue
        artifact = bound["repositories"][gate.repository]
        result = execution.result or {}
        if (
            not result.get("implementation_verified")
            or result.get("validated_artifact_hash") != artifact["tree"]
            or str(Path(execution.request["worktree_path"]).resolve()) != artifact["root"]
        ):
            continue
        for validation in result.get("validation_results", []):
            if validation["id"] == command.id and validation["argv"] == command.argv:
                return {**validation, "source_execution": execution.id}
    raise PermissionError("No unchanged independently validated AEO-2 artifact/command evidence")
