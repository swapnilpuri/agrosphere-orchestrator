"""Thin integration adapters over AEO-1B/1C/2/3/4/5; no alternative scheduler or provider."""

import hashlib
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import delivery, design, quality
from .autonomous_models import BudgetExceeded, Roadmap, StepResult
from .autonomous_store import AutonomousRun, event
from .configuration import RepositoryManifest, load_yaml
from .delivery_store import DeliveryRun
from .design_agents import RuleBasedArchitectureReviewer, TemplateDocumentationAgents
from .design_artifacts import LocalPlantUML, check_files, digest
from .design_models import DesignInput
from .execution import check_grant
from .orchestration import (
    TaskScheduler,
    load_plan,
    milestone_record,
    milestone_report,
    propose_plan,
    require_plan_approval,
)
from .orchestration_store import transaction
from .persistence import (
    DesignCase,
    DesignRevision,
    DesignScope,
    DesignValidation,
    Execution,
    import_plan,
)
from .recovery import next_milestone, reconcile
from .recovery_discovery import collect_repository, recover_milestones
from .recovery_models import RecoverySnapshot


class ExistingServices:
    def __init__(
        self, engine, settings, scheduler=None, validator=None, provider=None, renderer=None
    ):
        self.engine, self.settings = engine, settings
        self.scheduler = scheduler or TaskScheduler(engine, settings)
        self.validator, self.provider = validator, provider
        self.renderer = renderer or LocalPlantUML(settings.plantuml_jar, settings.java_executable)

    def approval_command(self, step, request):
        prefix = r".\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli "
        command = {
            "PREPARING_DESIGN": "milestone docs " + request.milestone,
            "PLANNING_TASKS": "milestone approve-plan " + request.milestone,
            "EXECUTING": "milestone execution-report " + request.milestone,
            "VERIFYING": "quality report --milestone " + request.milestone,
            "PREPARING_DELIVERY": "delivery plan <reviewed-manifest.json>",
            "OBSERVING_DELIVERY": "delivery status <delivery-run-id>",
        }.get(step, "milestone docs " + request.milestone)
        return prefix + command

    def discover(self, request):
        manifest = self.settings.repository_manifest
        roots = load_yaml(manifest, RepositoryManifest).resolve(manifest)
        confirmed = [r for r in roots if r.status == "confirmed"]
        if not confirmed or len({str(r.path).casefold() for r in confirmed}) != len(confirmed):
            raise ValueError("Missing or duplicate confirmed repository roots")
        workspace = self.settings.workspace_root.resolve()
        repositories, evidence = [], []
        for root in confirmed:
            if not root.path.is_relative_to(workspace) or root.path.is_symlink():
                raise ValueError("Confirmed repository escaped the configured workspace")
            # Inspect only exact manifest roots, never recursive fixture/worktree discovery.
            inventory, found = collect_repository(root.path)
            if inventory.get("error") or not inventory.get("is_git"):
                raise ValueError("Confirmed repository is unavailable: " + root.id)
            if Path(inventory["path"]).resolve() != root.path:
                raise ValueError("Repository identity differs from exact confirmed root")
            inventory["id"] = root.id
            repositories.append(inventory)
            evidence.extend(found)
        recovered = recover_milestones(repositories, evidence)
        snapshot = RecoverySnapshot(
            workspace=str(workspace),
            repositories=repositories,
            milestones=recovered,
            limitations=[
                "Manifest-bound read-only observation; claims are not acceptance or execution authority."
            ],
        )
        conflicts = [m.id for m in recovered if m.conflicts]
        return {
            "snapshot": snapshot.model_dump(mode="json"),
            "recovered_recommendation": next_milestone(snapshot),
            "conflicts": conflicts,
            "execution_eligible": False,
            "discovery_consistent": not conflicts,
            "selected_milestone": request.milestone,
            "selection_basis": "Explicit operator selection; dependencies must also pass registered task DAG and exact design/plan gates.",
            "numeric_advancement_authorized": False,
        }

    def eligibility(self, request, found):
        with Session(self.engine) as session:
            case = session.get(DesignCase, "agrosphere:" + request.milestone)
            scope = session.get(DesignScope, case.scope_id) if case and case.scope_id else None
            inputs = (
                DesignInput.model_validate(scope.payload["input"])
                if scope
                else request.requirements
            )
            if scope is None:
                return None  # Proposed requirements may be prepared; bind() still requires approved scope.
            if inputs is None:
                return "No authoritative scope; prepare proposed requirements before execution"
            if inputs.documentation_scope == "internal-orchestrator":
                return None
            path = self.settings.autonomous_roadmap
            if path is None:
                return "No approved roadmap configured; explicit selection cannot bypass dependency verification"
            path = path.resolve()
            roots = scope.payload["repositories"] if scope else {}
            approved_ref = next(
                (
                    c
                    for c in inputs.context
                    if c.repository in roots
                    and (Path(roots[c.repository]) / c.path).resolve() == path
                ),
                None,
            )
            if (
                not approved_ref
                or hashlib.sha256(path.read_bytes()).hexdigest() != approved_ref.sha256
            ):
                return "Roadmap is not bound to the exact requirements context"
            roadmap = load_yaml(path, Roadmap)
            entry = next((m for m in roadmap.milestones if m.id == request.milestone), None)
            if entry is None:
                return "Selected milestone is absent from approved roadmap"
            observed = {m["id"]: m for m in found["snapshot"]["milestones"]}
            for dependency in entry.depends_on:
                prior = session.get(DesignCase, "agrosphere:" + dependency)
                facts = observed.get(dependency, {})
                if (
                    not prior
                    or prior.state != "COMPLETED"
                    or facts.get("classification") != "COMPLETED"
                    or not facts.get("verified_acceptance_criteria")
                    or facts.get("conflicts")
                ):
                    return "Dependency lacks verified formal completion: " + dependency
            return None

    def gate_result(self, step, category, reason, command, evidence=None):
        return StepResult(
            next_step=step,
            evidence=evidence or {},
            checkpoint={"category": category, "reason": reason, "command": command},
        )

    def design_prepare(self, request):
        key = "agrosphere:" + request.milestone
        with Session(self.engine) as session:
            case = session.get(DesignCase, key)
            existing_scope = case.scope_id if case else None
        if request.requirements and existing_scope:
            with Session(self.engine) as session:
                prior = session.get(DesignScope, existing_scope)
                if prior.payload["input"] != request.requirements.model_dump(mode="json"):
                    return self.gate_result(
                        "PREPARING_DESIGN",
                        "scope-change",
                        "Supplied requirements differ from registered scope; explicitly review and register the changed scope through the existing workflow",
                        self.approval_command("PREPARING_DESIGN", request),
                    )
        if request.requirements:
            scope = design.register_requirements(
                self.engine,
                request.requirements,
                self.settings.repository_manifest,
                self.settings.role_registry,
            )
        else:
            scope = existing_scope
        if not scope:
            return self.gate_result(
                "PREPARING_DESIGN",
                "requirements-input",
                "Authoritative requirements/narratives are missing; supply an immutable DesignInput",
                self.approval_command("PREPARING_DESIGN", request),
            )
        with Session(self.engine) as session:
            case = session.get(DesignCase, key)
            try:
                design.require_approval(session, case, scope, "requirements")
            except PermissionError:
                return self.gate_result(
                    "PREPARING_DESIGN",
                    "requirements",
                    "Authenticated requirements approval is required for exact scope " + scope,
                    self.approval_command("PREPARING_DESIGN", request).replace(
                        "milestone docs", "milestone approve-requirements"
                    ),
                    {"scope_id": scope},
                )
            revision_id, state = case.revision_id, case.state
        if revision_id is None or state in {"DISCOVERED", "DESIGN_IN_PROGRESS"}:
            tool = (
                digest(self.settings.plantuml_jar.read_bytes().hex())
                if self.settings.plantuml_jar
                else "plantuml-unavailable"
            )
            revision_id = design.generate_design(
                self.engine, key, TemplateDocumentationAgents(), self.renderer, tool
            )
            validation = design.validate_design(self.engine, key, RuleBasedArchitectureReviewer())
            if not validation["passed"]:
                return self.gate_result(
                    "PREPARING_DESIGN",
                    "invalid-design",
                    "Formal design validation failed; resolve findings without changing approved scope silently",
                    self.approval_command("PREPARING_DESIGN", request),
                    validation,
                )
        # A durable revision may have survived interrupted publication.
        design.export_revision(self.engine, revision_id)
        with Session(self.engine) as session:
            case = session.get(DesignCase, key)
            revision = session.get(DesignRevision, revision_id)
            validation = (
                session.get(DesignValidation, case.validation_id) if case.validation_id else None
            )
            if not validation or not validation.payload["passed"]:
                return self.gate_result(
                    "PREPARING_DESIGN",
                    "invalid-design",
                    "Validation is missing or failed",
                    self.approval_command("PREPARING_DESIGN", request),
                )
            if check_files(design.artifacts_of(revision), revision.payload["repositories"]):
                raise PermissionError("Approved artifact integrity check failed")
            try:
                decision = design.require_approval(
                    session, case, revision.payload["bundle_digest"], "design"
                )
            except PermissionError:
                return self.gate_result(
                    "PREPARING_DESIGN",
                    "design",
                    "Authenticated approval of the validated exact design bundle is required",
                    self.approval_command("PREPARING_DESIGN", request).replace(
                        "milestone docs", "milestone approve-design"
                    ),
                    {
                        "scope_id": scope,
                        "revision_id": revision_id,
                        "bundle_digest": revision.payload["bundle_digest"],
                        "validation_id": validation.id,
                    },
                )
            inputs = DesignInput.model_validate(revision.payload["input"])
            refs = {
                "scope_id": scope,
                "revision_id": revision_id,
                "design_decision_id": decision.id,
                "bundle_digest": revision.payload["bundle_digest"],
                "validation_id": validation.id,
                "explanation_artifacts": [
                    a.model_dump(exclude={"content"}) for a in design.artifacts_of(revision)
                ],
            }
        if state == "COMPLETED":
            return StepResult(next_step="REPORTED", evidence={**refs, "already_completed": True})
        if state not in {"DESIGN_APPROVED", "IMPLEMENTATION_READY", "IMPLEMENTING"}:
            return self.gate_result(
                "PREPARING_DESIGN",
                "lifecycle",
                "Milestone lifecycle is not eligible for implementation continuation",
                self.approval_command("PREPARING_DESIGN", request),
                refs,
            )
        import_plan(self.engine, inputs.plan)
        if state == "DESIGN_APPROVED":
            design.implementation_ready(self.engine, key)
        return StepResult(next_step="PLANNING_TASKS", evidence=refs)

    def bind(self, request):
        found = self.discover(request)
        reason = self.eligibility(request, found)
        if found["conflicts"] or reason:
            raise PermissionError(reason or "Recovered dependency conflict")
        with Session(self.engine) as session:
            milestone = milestone_record(session, request.milestone)
            case = design.assert_design_gate(session, milestone)
            return {"scope_id": case.scope_id, "revision_id": case.revision_id}

    def planning(self, request):
        self.bind(request)
        if request.task_options is None:
            with Session(self.engine) as session:
                try:
                    milestone = milestone_record(session, request.milestone)
                    plan, _, revision = load_plan(session, milestone)
                    request.task_options = plan.tasks
                except (ValueError, PermissionError):
                    pass
        try:
            identity = propose_plan(
                self.engine, self.settings, request.milestone, request.task_options
            )
        except ValueError as exc:
            return self.gate_result(
                "PLANNING_TASKS",
                "plan-options",
                str(exc),
                r".\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli milestone plan "
                + request.milestone
                + " --options <reviewed-options.json>",
            )
        with Session(self.engine) as session:
            milestone = milestone_record(session, request.milestone)
            _, _, revision = load_plan(session, milestone)
            try:
                require_plan_approval(session, milestone, revision, self.settings)
            except PermissionError as exc:
                return self.gate_result(
                    "PLANNING_TASKS",
                    "plan",
                    str(exc),
                    self.approval_command("PLANNING_TASKS", request),
                    {"plan_id": identity},
                )
        return StepResult(
            next_step="EXECUTING", evidence={"plan_id": identity, **self.bind(request)}
        )

    def reserve_counter(self, value, name, maximum, amount=1):
        with transaction(self.engine) as session:
            run = session.get(AutonomousRun, value["run_id"])
            if run.state == "PAUSED" or run.current_operation != value["current_operation"]:
                raise BudgetExceeded("Run no longer owns operation")
            if run.usage[name] + amount > maximum:
                raise BudgetExceeded(name + " budget exhausted")
            run.usage = {**run.usage, name: run.usage[name] + amount}
            event(
                session,
                run,
                "budget.reserved",
                {"counter": name, "amount": amount, "total": run.usage[name]},
                run.current_operation,
            )

    async def executing(self, request, value, guard):
        self.bind(request)
        ids = await self.scheduler.prepare(request.milestone)
        pending = []
        with Session(self.engine) as session:
            for identity in ids:
                execution = session.get(Execution, identity)
                try:
                    check_grant(session, execution, self.settings)
                except PermissionError:
                    pending.append(identity)
        if pending:
            return self.gate_result(
                "EXECUTING",
                "execution",
                "Prepared exact executions require authenticated grants",
                None,
                {
                    "pending_executions": pending,
                    "commands": [
                        r".\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli agent approve --execution "
                        + i
                        for i in pending
                    ],
                },
            )
        batch = await self.scheduler.execute_ready_tasks(
            request.milestone, dispatch_guard=guard, max_batch_size=request.limits.max_concurrency
        )
        observed = milestone_report(self.engine, request.milestone)
        if observed["status"] == "COMPLETED":
            return StepResult(
                next_step="VERIFYING", evidence={"batch": batch, "scheduler": observed}
            )
        if not batch["results"]:
            return self.gate_result(
                "EXECUTING",
                "scheduler",
                "No independently verified progress; review dependency, grant, handoff and recovery blockers",
                self.approval_command("EXECUTING", request),
                {"batch": batch, "scheduler": observed},
            )
        return StepResult(next_step="EXECUTING", evidence={"batch": batch, "scheduler": observed})

    async def verifying(self, request, value):
        self.bind(request)
        with Session(self.engine) as session:
            milestone = milestone_record(session, request.milestone)
            try:
                policy = quality.active_policy(session, self.settings, milestone)
            except PermissionError as exc:
                return self.gate_result(
                    "VERIFYING",
                    "security-policy",
                    str(exc),
                    r".\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli quality activate --milestone "
                    + request.milestone,
                )
        remaining = (
            value["limits"]["max_seconds"]
            - (datetime.now(UTC) - datetime.fromisoformat(value["created_at"])).total_seconds()
        )
        if sum(g.timeout_seconds for g in policy.gates) > remaining:
            raise BudgetExceeded("Quality gate timeout reservation exceeds remaining deadline")
        readiness = quality.readiness(self.engine, self.settings, request.milestone, persist=False)
        # Reuse valid independent evidence; human approval must not require rerunning gates.
        if readiness["decision"] not in {"READY_FOR_APPROVAL", "APPROVED_FOR_DELIVERY"}:
            readiness = await quality.validate(
                self.engine, self.settings, request.milestone, validator=self.validator
            )
        if readiness["decision"] == "APPROVED_FOR_DELIVERY":
            return StepResult(next_step="PREPARING_DELIVERY", evidence={"quality": readiness})
        if readiness["decision"] == "READY_FOR_APPROVAL":
            return self.gate_result(
                "VERIFYING",
                "delivery-approval",
                "Independent quality passed; authenticated AEO-4 delivery approval is required",
                self.approval_command("VERIFYING", request),
                {"quality": readiness},
            )

        def reserve_repair(session, task):
            run = session.get(AutonomousRun, value["run_id"])
            if run.current_operation != value["current_operation"] or run.state != "VERIFYING":
                raise BudgetExceeded("Run no longer owns remediation")
            limit = min(value["limits"]["max_repairs"], self.settings.scheduler_max_repairs)
            if run.usage["repairs"] >= limit:
                raise BudgetExceeded("Repair budget exhausted")
            run.usage = {**run.usage, "repairs": run.usage["repairs"] + 1}
            event(
                session,
                run,
                "remediation.reserved",
                {"task_id": task.id, "validation": readiness.get("validation")},
                run.current_operation,
            )

        affected = quality.prepare_remediation(
            self.engine, self.settings, request.milestone, reservation_guard=reserve_repair
        )
        if affected:
            return StepResult(
                next_step="EXECUTING",
                evidence={
                    "quality": readiness,
                    "remediation_tasks": affected,
                    "new_exact_grants_required": True,
                },
            )
        return self.gate_result(
            "VERIFYING",
            "quality",
            "Quality or security failed; no policy-permitted repair is available",
            self.approval_command("VERIFYING", request),
            {"quality": readiness},
        )

    def delivery_planning(self, request):
        self.bind(request)
        if request.delivery_manifest is None:
            return self.gate_result(
                "PREPARING_DELIVERY",
                "delivery-manifest",
                "Supply a manifest bound to actual validated commits, repository/remote identities and publication branches",
                self.approval_command("PREPARING_DELIVERY", request),
            )
        identity = delivery.plan(self.engine, self.settings, request.delivery_manifest)
        return StepResult(next_step="OBSERVING_DELIVERY", evidence={"delivery_run": identity})

    def delivery_run(self, request):
        with Session(self.engine) as session:
            milestone = milestone_record(session, request.milestone)
            run = session.scalar(
                select(DeliveryRun).where(DeliveryRun.milestone_id == milestone.id)
            )
            if not run:
                raise ValueError("No persisted delivery manifest")
            if request.delivery_manifest and run.manifest != request.delivery_manifest.model_dump(
                mode="json"
            ):
                raise PermissionError("Persisted delivery manifest differs from run scope")
            return run.id

    def observing(self, request, value, allow_mutations=True):
        self.bind(request)
        identity = self.delivery_run(request)
        result = delivery.status(self.engine, identity)
        for unit in result["units"]:
            self.reserve_counter(value, "polls", value["limits"]["max_steps"])
            # Conservatively reserve the configured read timeout before each observation.
            self.reserve_counter(
                value,
                "poll_seconds",
                value["limits"]["max_poll_seconds"],
                self.settings.github_timeout_seconds,
            )
            result = delivery.observe(
                self.engine, self.settings, identity, unit["id"], provider=self.provider
            )
        if result["readiness"] == "READY_FOR_AUTHORIZED_MERGE":
            return StepResult(
                next_step="REPORTED",
                evidence={"delivery": result, "merge_executed": False, "formally_completed": False},
            )
        if any(u["state"] == "RECOVERY_REQUIRED" for u in result["units"]):
            return self.gate_result(
                "OBSERVING_DELIVERY",
                "recovery",
                "AEO-5 requires exact child recovery; no blind mutation replay",
                r".\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli delivery reconcile "
                + identity
                + " <unit>",
                {"delivery": result},
            )
        for unit in result["units"]:
            spec = next(u for u in request.delivery_manifest.units if u.id == unit["id"])
            observation = (unit.get("latest") or {}).get("observation") or {}
            action = (
                "prepare"
                if not delivery.worktree(self.settings, identity, unit["id"]).exists()
                else "push"
                if observation.get("branch_sha") != spec.head_sha
                else "create-pr"
                if not unit["pr_id"]
                else None
            )
            grant = request.publication_grants.get(unit["id"] + ":" + str(action))
            if action:
                if not allow_mutations or request.mode != "controlled-delivery" or not grant:
                    return self.gate_result(
                        "OBSERVING_DELIVERY",
                        "publication",
                        "Separate exact AEO-5 action grant required; mode alone grants nothing",
                        r".\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli delivery request-approval "
                        + identity
                        + " "
                        + unit["id"]
                        + " "
                        + action
                        + ' --justification "Review exact publication scope"',
                        {"delivery": result},
                    )
                if not self.settings.github_remote_writes:
                    return self.gate_result(
                        "OBSERVING_DELIVERY",
                        "publication",
                        "Remote writes remain disabled; an action grant does not enable publication configuration",
                        self.approval_command("OBSERVING_DELIVERY", request),
                        {"delivery": result},
                    )
                # The existing AEO-5 guard checks current scope, expiry, identity and remote-write settings.
                result = delivery.mutate(
                    self.engine,
                    self.settings,
                    identity,
                    unit["id"],
                    action,
                    grant,
                    provider=self.provider,
                )
                return StepResult(next_step="OBSERVING_DELIVERY", evidence={"delivery": result})
        return self.gate_result(
            "OBSERVING_DELIVERY",
            "ci-review",
            "Current CI/reviews/dependencies are not ready; resume within retained polling budget",
            self.approval_command("OBSERVING_DELIVERY", request),
            {"delivery": result},
        )

    async def perform(self, step, request, value, guard):
        if step in {
            "PLANNING_TASKS",
            "EXECUTING",
            "VERIFYING",
            "PREPARING_DELIVERY",
            "OBSERVING_DELIVERY",
        }:
            try:
                self.bind(request)
            except (PermissionError, ValueError) as exc:
                return self.gate_result(
                    step, "authorization", str(exc), self.approval_command(step, request)
                )
        if step == "RECONCILING":
            found = self.discover(request)
            if found["conflicts"]:
                return self.gate_result(
                    "RECONCILING",
                    "discovery-conflict",
                    "Conflicting recovered milestone evidence blocks eligibility",
                    None,
                    found,
                )
            reason = self.eligibility(request, found)
            if reason:
                return self.gate_result("RECONCILING", "eligibility", reason, None, found)
            identity = reconcile(self.engine, RecoverySnapshot.model_validate(found["snapshot"]))
            return StepResult(
                next_step="PREPARING_DESIGN", evidence={"recovery_snapshot": identity, **found}
            )
        if step == "PREPARING_DESIGN":
            return self.design_prepare(request)
        if step == "PLANNING_TASKS":
            return self.planning(request)
        if step == "EXECUTING":
            return await self.executing(request, value, guard)
        if step == "VERIFYING":
            return await self.verifying(request, value)
        if step == "PREPARING_DELIVERY":
            return self.delivery_planning(request)
        if step == "OBSERVING_DELIVERY":
            return self.observing(request, value)
        raise ValueError("Unknown autonomous workflow step")

    async def recover(self, step, request, value):
        if step == "RECONCILING":
            found = self.discover(request)
            if not found["conflicts"]:
                return StepResult(
                    next_step="PREPARING_DESIGN", evidence={"reobserved_discovery": found}
                )
        if step == "PREPARING_DESIGN":
            # Existing generation/export is content-addressed and never overwrites a revision.
            return self.design_prepare(request)
        if step == "EXECUTING":
            self.scheduler.reconcile(request.milestone)
            observed = milestone_report(self.engine, request.milestone)
            if observed["status"] == "COMPLETED":
                return StepResult(next_step="VERIFYING", evidence={"recovered_scheduler": observed})
        if step == "PLANNING_TASKS":
            try:
                with Session(self.engine) as session:
                    milestone = milestone_record(session, request.milestone)
                    plan, _, revision = load_plan(session, milestone)
                    design.assert_design_gate(session, milestone)
                    if request.task_options and plan.tasks != request.task_options:
                        return None
                    try:
                        require_plan_approval(session, milestone, revision, self.settings)
                    except PermissionError:
                        return self.gate_result(
                            "PLANNING_TASKS",
                            "plan",
                            "Recovered exact plan requires authenticated approval",
                            self.approval_command("PLANNING_TASKS", request),
                            {"recovered_plan_id": revision.id},
                        )
                    return StepResult(
                        next_step="EXECUTING", evidence={"recovered_plan_id": revision.id}
                    )
            except (PermissionError, ValueError):
                return None
        if step == "VERIFYING":
            observed = quality.readiness(
                self.engine, self.settings, request.milestone, persist=False
            )
            if observed["decision"] == "READY_FOR_APPROVAL":
                return self.gate_result(
                    "VERIFYING",
                    "delivery-approval",
                    "Recovered independent validation requires authenticated AEO-4 delivery approval",
                    self.approval_command("VERIFYING", request),
                    {"recovered_quality": observed},
                )
            if observed["decision"] == "APPROVED_FOR_DELIVERY":
                return StepResult(
                    next_step="PREPARING_DELIVERY", evidence={"recovered_quality": observed}
                )
        if step == "PREPARING_DELIVERY":
            identity = self.delivery_run(request)
            return StepResult(
                next_step="OBSERVING_DELIVERY", evidence={"recovered_delivery_run": identity}
            )
        if step == "OBSERVING_DELIVERY":
            return self.observing(request, value, allow_mutations=False)
        # Uncertain planning, remediation or child execution needs existing child recovery.
        return None
