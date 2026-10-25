"""Deterministic dependency scheduling. Agents recommend; persisted evidence authorizes readiness."""

import asyncio
import hashlib
import json
from collections import Counter
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from .configuration import RepositoryManifest, RoleRegistry, load_yaml
from .design import assert_design_gate, canonical
from .execution import cancel_execution, check_grant, queue_execution, run_execution
from .execution_context import safe_relative
from .execution_models import ExecutionMode, ExecutionPolicy
from .orchestration_models import ArtifactReference, ExecutionPlan, FailureKind, TaskOptions
from .orchestration_store import (
    OrchestrationControl,
    OrchestrationEvidence,
    PlanRevision,
    TaskClaim,
    acquire,
    evidence,
    expiry,
    release,
    transaction,
)
from .persistence import Execution, Milestone, Task, now


def milestone_record(session, external_id, project="agrosphere"):
    milestone = session.scalar(
        select(Milestone).where(
            Milestone.external_id == external_id, Milestone.project_id == project
        )
    )
    if milestone is None:
        raise ValueError("Unknown imported milestone")
    return milestone


def load_plan(session, milestone):
    control = session.get(OrchestrationControl, milestone.id)
    if control is None:
        raise ValueError("No validated scheduling plan")
    revision = session.get(PlanRevision, control.plan_id)
    return ExecutionPlan.model_validate(revision.payload), control, revision


def verify_artifact(settings, ref, session=None, milestone=None):
    repositories = {
        r.id: r
        for r in load_yaml(settings.repository_manifest, RepositoryManifest).resolve(
            settings.repository_manifest
        )
    }
    owner = repositories.get(ref.repository)
    if owner is None or owner.status != "confirmed":
        raise PermissionError("Artifact repository is not confirmed")
    artifact_root = owner.path
    if ref.producer:
        if session is None or milestone is None:
            raise PermissionError("Producer artifact requires persisted execution context")
        producer = session.scalar(
            select(Task).where(Task.milestone_id == milestone.id, Task.external_id == ref.producer)
        )
        execution = session.scalar(
            select(Execution)
            .where(
                Execution.task_id == producer.id if producer else False,
                Execution.state == "SUCCEEDED",
            )
            .order_by(Execution.created_at.desc())
        )
        if (
            producer is None
            or producer.state != "succeeded"
            or execution is None
            or execution.task_id != producer.id
            or execution.state != "SUCCEEDED"
            or execution.request["source_head"] != ref.revision
            or not execution.result
            or not execution.result.get("implementation_verified")
        ):
            raise PermissionError("Artifact producer lacks verified write evidence")
        artifact_root = Path(execution.request["worktree_path"])
    else:
        from .repositories import inspect_repository

        if inspect_repository(owner).head != ref.revision:
            raise PermissionError("Artifact commit revision changed")
    p = safe_relative(artifact_root, ref.path)
    if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != ref.sha256:
        raise PermissionError("Handoff artifact is missing or invalidated")
    return ref.model_dump()


def propose_plan(engine, settings, milestone_id, options=None, project="agrosphere"):
    with transaction(engine) as session:
        milestone = milestone_record(session, milestone_id, project)
        case = assert_design_gate(session, milestone)
        from .models import MilestoneSpec

        spec = MilestoneSpec.model_validate(milestone.spec)
        roles = load_yaml(settings.role_registry, RoleRegistry).by_id()
        repositories = {
            r.id
            for r in load_yaml(settings.repository_manifest, RepositoryManifest).resolve(
                settings.repository_manifest
            )
            if r.status == "confirmed"
        }
        if options is None:
            options = {}
            for task in spec.tasks:
                if task.operation in {"code-write", "document"}:
                    raise ValueError(
                        "Write planning requires explicit paths and validation commands"
                    )
                options[task.id] = TaskOptions()
        for task in spec.tasks:
            role = roles.get(task.role)
            if (
                role is None
                or task.operation not in role.allowed_operations
                or task.repository not in repositories
                or task.repository not in role.allowed_repositories
            ):
                raise PermissionError(
                    "Task assignment exceeds registered role/repository permissions"
                )
        execution_policy = load_yaml(settings.execution_policy, ExecutionPolicy)
        commands = {c.id for c in execution_policy.validation_commands}
        for identity, option in options.items():
            if not set(option.validation_commands) <= commands:
                raise PermissionError("Plan validation command is not administrator allowlisted")
            if (
                option.specialization
                and option.specialization
                not in roles[next(t.role for t in spec.tasks if t.id == identity)].specializations
            ):
                raise PermissionError("Plan specialization is not registered")
        prior = list(
            session.scalars(select(PlanRevision).where(PlanRevision.milestone_id == milestone.id))
        )
        plan = ExecutionPlan(
            milestone=spec,
            design_revision=case.revision_id,
            version=max([p.version for p in prior], default=0) + 1,
            tasks=options,
        )
        current_control = session.get(OrchestrationControl, milestone.id)
        for previous in prior:
            payload = {**plan.model_dump(mode="json"), "version": previous.version}
            if (
                payload == previous.payload
                and current_control
                and current_control.plan_id == previous.id
            ):
                return previous.id
        if session.scalar(select(TaskClaim).join(Task).where(Task.milestone_id == milestone.id)):
            raise PermissionError("Reconcile active claims before revising a plan")
        identity = hashlib.sha256(canonical(plan.model_dump(mode="json")).encode()).hexdigest()
        session.add(
            PlanRevision(
                id=identity,
                milestone_id=milestone.id,
                version=plan.version,
                payload=plan.model_dump(mode="json"),
            )
        )
        session.flush()
        control = session.get(OrchestrationControl, milestone.id)
        if control:
            control.plan_id = identity
        else:
            session.add(
                OrchestrationControl(milestone_id=milestone.id, plan_id=identity, paused=False)
            )
        evidence(session, milestone.id, None, "plan.proposed", {"plan_id": identity})
        return identity


def approve_plan(engine, settings, milestone_id, verifier, project="agrosphere"):
    with Session(engine) as session:
        milestone = milestone_record(session, milestone_id, project)
        _, _, revision = load_plan(session, milestone)
        identity = revision.id
    actor = verifier.verify(identity + ":approve-plan", "approved")
    if actor not in settings.execution_approvers:
        raise PermissionError("Authenticated execution approver required")
    with transaction(engine) as session:
        milestone = milestone_record(session, milestone_id, project)
        _, _, revision = load_plan(session, milestone)
        if revision.id != identity:
            raise PermissionError("Plan changed during human review")
        assert_design_gate(session, milestone)
        evidence(
            session, milestone.id, None, "plan.approved", {"plan_id": identity, "actor": actor}
        )


def require_plan_approval(session, milestone, revision, settings):
    approved = [
        e
        for e in session.scalars(
            select(OrchestrationEvidence).where(
                OrchestrationEvidence.milestone_id == milestone.id,
                OrchestrationEvidence.kind == "plan.approved",
            )
        )
        if e.payload["plan_id"] == revision.id
        and e.payload["actor"] in settings.execution_approvers
    ]
    if not approved:
        raise PermissionError("Scheduling plan requires human approval")


def classify(result):
    if result.status == "TIMED_OUT":
        return FailureKind.EXECUTION_TIMEOUT
    code = result.error.code if result.error else ""
    return {
        "policy": FailureKind.SECURITY_POLICY_VIOLATION,
        "artifact-policy": FailureKind.SECURITY_POLICY_VIOLATION,
        "context-invalidated": FailureKind.APPROVAL_REQUIRED,
        "authentication": FailureKind.APPROVAL_REQUIRED,
        "output-parse": FailureKind.INVALID_AGENT_OUTPUT,
        "runtime-exit": FailureKind.TRANSIENT_RUNTIME_ERROR,
        "execution-error": FailureKind.TRANSIENT_RUNTIME_ERROR,
    }.get(
        code,
        FailureKind.CODE_VALIDATION_FAILURE
        if result.validation_results
        else FailureKind.UNKNOWN_FAILURE,
    )


class TaskScheduler:
    def __init__(self, engine, settings, adapter=None, isolation_probe=None):
        self.engine, self.settings = engine, settings
        self.adapter, self.isolation_probe = adapter, isolation_probe
        if (
            min(
                settings.scheduler_max_concurrency,
                settings.scheduler_per_agent,
                settings.scheduler_per_repository,
            )
            < 1
        ):
            raise ValueError("Scheduler limits must be positive")
        if not 0 <= settings.scheduler_max_repairs <= 3:
            raise ValueError("Automatic repairs must be bounded by three")

    def _ready(self, session, milestone):
        plan, control, revision = load_plan(session, milestone)
        require_plan_approval(session, milestone, revision, self.settings)
        case = assert_design_gate(session, milestone)
        if case.revision_id != plan.design_revision:
            raise PermissionError("Approved design revision differs from scheduling plan")
        tasks = {
            t.external_id: t
            for t in session.scalars(select(Task).where(Task.milestone_id == milestone.id))
        }
        records = list(
            session.scalars(
                select(OrchestrationEvidence).where(
                    OrchestrationEvidence.milestone_id == milestone.id
                )
            )
        )
        ready, blocked = [], {}
        for spec in sorted(plan.milestone.tasks, key=lambda t: (-plan.tasks[t.id].priority, t.id)):
            task = tasks[spec.id]
            if task.state in {"succeeded", "cancelled", "reconciliation_required"}:
                continue
            reason = None
            if control.paused:
                reason = "paused"
            elif session.get(TaskClaim, task.id):
                reason = "claimed or reconciliation required"
            elif any(
                tasks[d].state != "succeeded"
                or not any(e.task_id == tasks[d].id and e.kind == "task.verified" for e in records)
                for d in spec.depends_on
            ):
                reason = "dependency lacks verified completion"
            elif task.state == "failed":
                attempts = [e for e in records if e.task_id == task.id and e.kind == "task.result"]
                limit = min(plan.tasks[spec.id].max_repairs, self.settings.scheduler_max_repairs)
                last = attempts[-1].payload if attempts else {}
                repairable = last.get("failure") in {
                    FailureKind.TRANSIENT_RUNTIME_ERROR.value,
                    FailureKind.CODE_VALIDATION_FAILURE.value,
                    FailureKind.INVALID_AGENT_OUTPUT.value,
                    FailureKind.EXECUTION_TIMEOUT.value,
                }
                if (
                    not repairable
                    or len(attempts) > limit
                    or plan.tasks[spec.id].mode != ExecutionMode.READ_ONLY
                ):
                    reason = "retry exhausted or explicit write recovery approval required"
            if reason is None:
                try:
                    for ref in plan.tasks[spec.id].inputs:
                        verify_artifact(self.settings, ref, session, milestone)
                        if ref.producer and not any(
                            e.kind == "handoff.published"
                            and e.payload.get("destination") == task.id
                            and ref.model_dump() in e.payload.get("artifacts", [])
                            for e in records
                        ):
                            raise PermissionError("Required persisted handoff is missing")
                except (OSError, PermissionError) as exc:
                    reason = str(exc)
            if reason:
                blocked[spec.id] = reason
            else:
                ready.append(task.id)
        return plan, tasks, ready, blocked

    async def schedule(self, milestone_id, project="agrosphere"):
        with transaction(self.engine) as session:
            milestone = milestone_record(session, milestone_id, project)
            _, tasks, ready, blocked = self._ready(session, milestone)
            for task in tasks.values():
                if task.id in ready and task.state == "pending":
                    task.state = "ready"
            payload = {"ready": ready, "blocked": blocked}
            evidence(session, milestone.id, None, "schedule", payload)
            return payload

    async def prepare(self, milestone_id, project="agrosphere"):
        await self.schedule(milestone_id, project)
        prepared = []
        with Session(self.engine) as session:
            milestone = milestone_record(session, milestone_id, project)
            plan, tasks, ready, _ = self._ready(session, milestone)
            work = [(t, plan.tasks[t.external_id]) for t in tasks.values() if t.id in ready]
        for task, options in work:
            with Session(self.engine) as session:
                pending = session.scalar(
                    select(Execution).where(
                        Execution.task_id == task.id, Execution.state == "AWAITING_APPROVAL"
                    )
                )
                if pending:
                    prepared.append(pending.id)
                    continue
            with Session(self.engine) as session:
                prior = session.scalar(
                    select(Execution)
                    .where(
                        Execution.task_id == task.id, Execution.state.in_(["FAILED", "TIMED_OUT"])
                    )
                    .order_by(Execution.created_at.desc())
                )
                parent = prior.id if prior else None
            identity = queue_execution(
                self.engine,
                self.settings,
                task.id,
                mode=options.mode,
                scopes=options.allowed_paths,
                specialization=options.specialization,
                command_ids=options.validation_commands,
                timeout=options.timeout_seconds,
                parent=parent,
                instructions="Review preserved failure evidence and repair within the same approved scope. "
                + task.spec["title"]
                if parent
                else None,
            )
            if parent:
                with transaction(self.engine) as session:
                    evidence(
                        session,
                        task.milestone_id,
                        task.id,
                        "repair.prepared",
                        {
                            "parent_execution_id": parent,
                            "execution_id": identity,
                            "max_repairs": min(
                                options.max_repairs, self.settings.scheduler_max_repairs
                            ),
                            "new_exact_grant_required": True,
                        },
                    )
            prepared.append(identity)
        return prepared

    async def execute_ready_tasks(self, milestone_id, project="agrosphere"):
        owner = str(uuid4())
        selected = []
        with transaction(self.engine) as session:
            milestone = milestone_record(session, milestone_id, project)
            plan, tasks, ready, blocked = self._ready(session, milestone)
            claims = list(session.scalars(select(TaskClaim)))
            active_tasks = [session.get(Task, c.task_id) for c in claims]
            role_counts = Counter(t.spec["role"] for t in active_tasks)
            repo_counts = Counter(t.spec["repository"] for t in active_tasks)
            capacity = max(0, self.settings.scheduler_max_concurrency - len(claims))
            for task_id in ready:
                if len(selected) >= capacity:
                    break
                task = next(t for t in tasks.values() if t.id == task_id)
                options = plan.tasks[task.external_id]
                role, repository = task.spec["role"], task.spec["repository"]
                if role_counts[role] >= self.settings.scheduler_per_agent:
                    continue
                if repo_counts[repository] >= self.settings.scheduler_per_repository:
                    continue
                execution = session.scalar(
                    select(Execution).where(
                        Execution.task_id == task_id, Execution.state == "AWAITING_APPROVAL"
                    )
                )
                if execution is None:
                    blocked[task.external_id] = "prepare exact execution and obtain human grant"
                    continue
                try:
                    request, _ = check_grant(session, execution, self.settings)
                except PermissionError as exc:
                    blocked[task.external_id] = str(exc)
                    continue
                if (
                    request.mode != options.mode
                    or request.allowed_file_scopes != options.allowed_paths
                    or request.validation_commands != options.validation_commands
                    or request.design_revision != plan.design_revision
                ):
                    blocked[task.external_id] = "execution request differs from approved plan"
                    continue
                claim_owner = owner + ":" + task_id
                resources = [
                    "repository:" + repository,
                    *("shared:" + r for r in options.resources),
                ]
                if not acquire(
                    session,
                    task_id,
                    claim_owner,
                    resources,
                    options.mode != ExecutionMode.READ_ONLY,
                    options.timeout_seconds + 120,
                ):
                    blocked[task.external_id] = "resource conflict or stale lease"
                    continue
                session.add(
                    TaskClaim(
                        task_id=task_id,
                        owner=claim_owner,
                        execution_id=execution.id,
                        expires_at=expiry(options.timeout_seconds + 120),
                        reconciliation_required=False,
                    )
                )
                for ref in options.inputs:
                    evidence(
                        session,
                        milestone.id,
                        task_id,
                        "handoff.acknowledged",
                        {"artifact": ref.model_dump(), "execution_id": execution.id},
                    )
                role_counts[role] += 1
                repo_counts[repository] += 1
                selected.append((task_id, execution.id, claim_owner, options))
            evidence(
                session,
                milestone.id,
                None,
                "batch.claimed",
                {"batch_id": owner, "executions": [s[1] for s in selected], "blocked": blocked},
            )
        results = await asyncio.gather(*(self._execute(*s) for s in selected))
        return {"batch_id": owner, "results": results, "blocked": blocked}

    async def _execute(self, task_id, execution_id, owner, options):
        kwargs = {"adapter": self.adapter}
        if self.isolation_probe:
            kwargs["isolation_probe"] = self.isolation_probe
        try:
            result = await run_execution(self.engine, self.settings, execution_id, **kwargs)
        except BaseException as exc:
            # No inferred termination: retain locks until the execution/session reconciler proves it.
            with transaction(self.engine) as session:
                claim = session.get(TaskClaim, task_id)
                if claim and claim.owner == owner:
                    claim.reconciliation_required = True
                    task = session.get(Task, task_id)
                    task.state = "reconciliation_required"
                    evidence(
                        session,
                        task.milestone_id,
                        task_id,
                        "reconciliation.required",
                        {"execution_id": execution_id, "error_type": type(exc).__name__},
                    )
            if isinstance(exc, asyncio.CancelledError):
                cancel_execution(self.engine, execution_id)
                raise
            return {"task_id": task_id, "state": "reconciliation_required"}
        with transaction(self.engine) as session:
            task = session.get(Task, task_id)
            claim = session.get(TaskClaim, task_id)
            if not claim or claim.owner != owner:
                raise PermissionError("Task claim ownership changed")
            accepted = task.state == "succeeded" and result.status == "SUCCEEDED"
            if options.mode != ExecutionMode.READ_ONLY:
                accepted = accepted and result.implementation_verified
            for output in options.expected_outputs:
                target = safe_relative(
                    Path(session.get(Execution, execution_id).request["worktree_path"]), output
                )
                if not target.is_file():
                    accepted = False
            if not accepted and task.state != "cancelled":
                task.state = "failed"
            evidence(
                session,
                task.milestone_id,
                task_id,
                "task.result",
                {
                    "execution_id": execution_id,
                    "result": result.model_dump(mode="json"),
                    "failure": None if accepted else classify(result).value,
                },
            )
            if accepted:
                evidence(
                    session,
                    task.milestone_id,
                    task_id,
                    "task.verified",
                    {"execution_id": execution_id, "evidence": result.evidence_references},
                )
            release(session, owner)
            session.delete(claim)
            milestone = session.get(Milestone, task.milestone_id)
            milestone_internal_id = milestone.id
            external_id, project, source = (
                milestone.external_id,
                milestone.project_id,
                task.external_id,
            )
            plan, _, _ = load_plan(session, milestone)
            destinations = [
                (identity, [ref for ref in option.inputs if ref.producer == source])
                for identity, option in plan.tasks.items()
            ]
        if accepted:
            for destination, refs in destinations:
                if refs:
                    try:
                        publish_handoff(
                            self.engine,
                            self.settings,
                            external_id,
                            source,
                            destination,
                            [r.model_dump() for r in refs],
                            result.summary,
                            project,
                        )
                    except (PermissionError, OSError) as exc:
                        with transaction(self.engine) as session:
                            evidence(
                                session,
                                milestone_internal_id,
                                task_id,
                                "handoff.failed",
                                {"destination": destination, "reason": str(exc)},
                            )
        return {"task_id": task_id, "execution_id": execution_id, "accepted": accepted}

    async def execute(self, milestone_id, project="agrosphere"):
        # Finite drain. Newly eligible tasks are prepared, then await exact human grants.
        batches = []
        for _ in range(1000):
            await self.prepare(milestone_id, project)
            batch = await self.execute_ready_tasks(milestone_id, project)
            batches.append(batch)
            if not batch["results"]:
                return batches
        raise RuntimeError("Batch budget exhausted; inspect milestone report")

    async def pause(self, milestone_id, project="agrosphere"):
        active = []
        with transaction(self.engine) as session:
            milestone = milestone_record(session, milestone_id, project)
            _, control, _ = load_plan(session, milestone)
            control.paused = True
            active = list(
                session.scalars(
                    select(TaskClaim.execution_id)
                    .join(Task)
                    .where(Task.milestone_id == milestone.id)
                )
            )
            evidence(session, milestone.id, None, "paused", {})
        for execution_id in active:
            if execution_id:
                cancel_execution(self.engine, execution_id)

    async def resume(self, milestone_id, project="agrosphere"):
        self.reconcile(milestone_id, project)
        with transaction(self.engine) as session:
            milestone = milestone_record(session, milestone_id, project)
            _, control, _ = load_plan(session, milestone)
            if session.scalar(
                select(TaskClaim).join(Task).where(Task.milestone_id == milestone.id)
            ):
                raise PermissionError("Outstanding claims require reconciliation")
            deviations = list(
                session.scalars(
                    select(OrchestrationEvidence).where(
                        OrchestrationEvidence.milestone_id == milestone.id,
                        OrchestrationEvidence.kind == "design.deviation",
                    )
                )
            )
            if deviations:
                _, _, revision = load_plan(session, milestone)
                if revision.created_at <= max(d.created_at for d in deviations):
                    raise PermissionError("Reconcile and approve a new plan after design deviation")
                require_plan_approval(session, milestone, revision, self.settings)
                assert_design_gate(session, milestone)
            control.paused = False
            evidence(session, milestone.id, None, "resumed", {})

    def reconcile(self, milestone_id, project="agrosphere"):
        from .execution_sessions import CodexSessionManager

        CodexSessionManager(self.engine).reconcile()
        results = []
        with transaction(self.engine) as session:
            milestone = milestone_record(session, milestone_id, project)
            for claim in session.scalars(
                select(TaskClaim).join(Task).where(Task.milestone_id == milestone.id)
            ):
                execution = (
                    session.get(Execution, claim.execution_id) if claim.execution_id else None
                )
                if execution and execution.state in {"PREPARING", "RUNNING"}:
                    results.append({"task_id": claim.task_id, "state": "still active"})
                    continue
                task = session.get(Task, claim.task_id)
                # A persisted result can establish completion. Never replay an uncertain write.
                if (
                    execution
                    and execution.result
                    and task.state in {"succeeded", "failed", "cancelled"}
                ):
                    release(session, claim.owner)
                    session.delete(claim)
                    evidence(
                        session,
                        milestone.id,
                        task.id,
                        "claim.reconciled",
                        {"execution_id": execution.id, "state": task.state},
                    )
                    if task.state == "succeeded":
                        evidence(
                            session,
                            milestone.id,
                            task.id,
                            "task.verified",
                            {"execution_id": execution.id, "recovered": True},
                        )
                else:
                    task.state = "reconciliation_required"
                    claim.reconciliation_required = True
                    evidence(
                        session,
                        milestone.id,
                        task.id,
                        "reconciliation.required",
                        {"execution_id": claim.execution_id, "expired": claim.expires_at <= now()},
                    )
                results.append({"task_id": task.id, "state": task.state})
        return results


def publish_handoff(
    engine,
    settings,
    milestone_id,
    source,
    destination,
    artifacts,
    summary,
    project="agrosphere",
    known_issues=None,
):
    refs = [ArtifactReference.model_validate(a) for a in artifacts]
    with transaction(engine) as session:
        milestone = milestone_record(session, milestone_id, project)
        plan, _, revision = load_plan(session, milestone)
        require_plan_approval(session, milestone, revision, settings)
        assert_design_gate(session, milestone)
        tasks = {
            t.external_id: t
            for t in session.scalars(select(Task).where(Task.milestone_id == milestone.id))
        }
        src, dst = tasks[source], tasks[destination]
        if source not in dst.spec["depends_on"] or src.state != "succeeded":
            raise PermissionError("Handoff requires a completed explicit prerequisite")
        verified = session.scalar(
            select(OrchestrationEvidence).where(
                OrchestrationEvidence.task_id == src.id,
                OrchestrationEvidence.kind == "task.verified",
            )
        )
        if not verified:
            raise PermissionError("Handoff requires verified execution evidence")
        for ref in refs:
            if ref.producer != source or ref not in plan.tasks[destination].inputs:
                raise PermissionError("Handoff artifact is outside the approved plan")
            verify_artifact(settings, ref, session, milestone)
        return evidence(
            session,
            milestone.id,
            src.id,
            "handoff.published",
            {
                "source": src.id,
                "source_role": src.spec["role"],
                "destination": dst.id,
                "destination_role": dst.spec["role"],
                "milestone": milestone_id,
                "context_summary": summary,
                "artifacts": [r.model_dump() for r in refs],
                "commit_references": [r.revision for r in refs],
                "completion_criteria": dst.spec["acceptance_criteria"],
                "validation_evidence": verified.payload,
                "known_issues": known_issues or [],
                "status": "published",
            },
        )


def milestone_report(engine, milestone_id, project="agrosphere"):
    with Session(engine) as session:
        milestone = milestone_record(session, milestone_id, project)
        plan, control, revision = load_plan(session, milestone)
        tasks = [
            {
                "id": t.id,
                "task": t.external_id,
                "role": t.spec["role"],
                "repository": t.spec["repository"],
                "state": t.state,
            }
            for t in session.scalars(select(Task).where(Task.milestone_id == milestone.id))
        ]
        records = [
            {
                "id": e.id,
                "task_id": e.task_id,
                "kind": e.kind,
                "created_at": e.created_at,
                "payload": e.payload,
            }
            for e in session.scalars(
                select(OrchestrationEvidence)
                .where(OrchestrationEvidence.milestone_id == milestone.id)
                .order_by(OrchestrationEvidence.created_at, OrchestrationEvidence.id)
            )
        ]
        verified = {e["task_id"] for e in records if e["kind"] == "task.verified"}
        completed = all(t["state"] == "succeeded" and t["id"] in verified for t in tasks)
        report = {
            "milestone": milestone_id,
            "project": project,
            "plan_id": revision.id,
            "version": plan.version,
            "plan": plan.model_dump(mode="json"),
            "paused": control.paused,
            "status": "COMPLETED" if completed else "INCOMPLETE",
            "tasks": tasks,
            "events": records,
            "counts": dict(Counter(t["state"] for t in tasks)),
            "parallel_batches": [
                e["payload"]
                for e in records
                if e["kind"] == "batch.claimed" and len(e["payload"]["executions"]) > 1
            ],
            "next_actions": []
            if completed
            else [
                "Review blockers and exact pending execution grants",
                "Reconcile uncertain operations before any write recovery",
            ],
        }
        return report


async def propose_deviation(
    engine, settings, milestone_id, description, impact, project="agrosphere"
):
    scheduler = TaskScheduler(engine, settings)
    await scheduler.pause(milestone_id, project)
    with transaction(engine) as session:
        milestone = milestone_record(session, milestone_id, project)
        return evidence(
            session,
            milestone.id,
            None,
            "design.deviation",
            {
                "proposal": description,
                "impact": impact,
                "approval": "required",
                "next_action": "Revise approved design and reconcile execution plan before resume",
            },
        )


def markdown_report(report):
    lines = [
        f"# Milestone {report['milestone']}",
        "",
        f"Status: {report['status']}",
        f"Plan revision: {report['plan_id']}",
        "",
        "| Task | Role | State |",
        "| --- | --- | --- |",
    ]
    lines += [f"| {t['task']} | {t['role']} | {t['state']} |" for t in report["tasks"]]
    return "\n".join(lines) + "\n\n## Evidence\n\n" + json.dumps(report["events"], indent=2) + "\n"
