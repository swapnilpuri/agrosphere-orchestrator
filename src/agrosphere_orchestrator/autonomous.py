"""Deterministic, bounded coordination; existing services remain authority owners."""

import time
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from .autonomous_models import AutonomousRequest, BudgetExceeded, RunLimits, StepResult
from .autonomous_store import (
    AutonomousEvent,
    AutonomousOperation,
    AutonomousRun,
    checkpoint,
    event,
    report,
)
from .design import canonical
from .design_artifacts import digest
from .orchestration_store import transaction
from .persistence import Execution


class AutonomousMilestoneController:
    def __init__(self, engine, settings, services=None, fault=None):
        self.engine, self.settings = engine, settings
        self.started_at, self.started_clock = datetime.now(UTC), time.monotonic()
        if services is None:
            from .autonomous_services import ExistingServices

            services = ExistingServices(engine, settings)
        self.services, self.fault = services, fault or (lambda boundary, operation: None)

    def limits(self, requested):
        data = requested.model_dump()
        for name in data:
            if name == "max_milestones":
                continue
            configured = getattr(self.settings, "autonomous_" + name)
            if name == "max_model_cost":
                caps = [v for v in (data[name], configured) if v is not None]
                data[name] = min(caps) if caps else None
            else:
                data[name] = min(data[name], configured)
        return RunLimits.model_validate(data)

    def plan(self, request):
        request = AutonomousRequest.model_validate(request.model_dump())
        return {
            "milestone": request.milestone,
            "mode": "dry-run",
            "mutations": False,
            "limits": self.limits(request.limits).model_dump(),
            "discovery": self.services.discover(request),
            "next_action": "Register/verify exact requirements and design; local mode grants no execution authority.",
            "formally_completed": False,
        }

    def start(self, request, identity=None):
        request = AutonomousRequest.model_validate(request.model_dump())
        if request.mode == "dry-run":
            return self.plan(request)
        request.limits = self.limits(request.limits)
        payload = request.model_dump(mode="json")
        hashed = digest(canonical(payload))
        identity = identity or str(uuid4())
        with transaction(self.engine) as session:
            existing = session.get(AutonomousRun, identity)
            if existing:
                if existing.request_hash != hashed:
                    raise ValueError("Run ID cannot change scope or reset budgets")
            else:
                active = session.scalar(
                    select(AutonomousRun).where(AutonomousRun.active_milestone == request.milestone)
                )
                if active:
                    raise PermissionError("Resume the existing active run: " + active.id)
                run = AutonomousRun(
                    id=identity,
                    milestone=request.milestone,
                    request_hash=hashed,
                    request=payload,
                    state="PLANNED",
                    step="RECONCILING",
                    current_operation=None,
                    active_milestone=request.milestone,
                    checkpoint=None,
                    references={},
                    usage={
                        "steps": 0,
                        "invocations": 0,
                        "attempts": 0,
                        "repairs": 0,
                        "polls": 0,
                        "poll_seconds": 0.0,
                        "tasks": [],
                        "tokens": None,
                        "model_cost": None,
                    },
                )
                session.add(run)
                session.flush()
                event(session, run, "created", {"request_hash": hashed, "mode": request.mode})
        return report(self.engine, identity)

    def elapsed(self, run):
        created = datetime.fromisoformat(run.created_at)
        wall = (datetime.now(UTC) - created).total_seconds()
        monotonic = (
            max(0, (self.started_at - created).total_seconds())
            + time.monotonic()
            - self.started_clock
        )
        return max(0, wall, monotonic, run.usage.get("elapsed_seconds", 0))

    def remaining(self, run):
        return run.request["limits"]["max_seconds"] - self.elapsed(run)

    def retain_elapsed(self, run):
        run.usage = {**run.usage, "elapsed_seconds": self.elapsed(run)}

    def dispatch_guard(self, identity, operation):
        def reserve(session, execution, request, options):
            run = session.get(AutonomousRun, identity)
            if run.current_operation != operation or run.state != "EXECUTING":
                raise BudgetExceeded("Run paused, changed or no longer owns dispatch")
            self.retain_elapsed(run)
            bounds, usage = run.request["limits"], dict(run.usage)
            if bounds["max_model_cost"] is not None:
                raise BudgetExceeded(
                    "Model cost is unknown; configured monetary cap cannot be enforced"
                )
            timeout = max(options.timeout_seconds, request.timeout_seconds)
            commands = getattr(request, "validation_commands", [])
            if commands:
                from .configuration import load_yaml
                from .execution_models import ExecutionPolicy

                policy = load_yaml(self.settings.execution_policy, ExecutionPolicy)
                timeout += sum(
                    c.timeout_seconds for c in policy.validation_commands if c.id in commands
                )
            if timeout > self.remaining(run):
                raise BudgetExceeded(
                    "Approved execution and validation timeout exceeds remaining run deadline"
                )
            if (
                usage["invocations"] >= bounds["max_invocations"]
                or usage["attempts"] >= bounds["max_attempts"]
            ):
                raise BudgetExceeded("Invocation or attempt budget exhausted")
            tasks = set(usage["tasks"]) | {execution.task_id}
            if len(tasks) > bounds["max_tasks"]:
                raise BudgetExceeded("Task budget exhausted")
            usage.update(
                invocations=usage["invocations"] + 1,
                attempts=usage["attempts"] + 1,
                tasks=sorted(tasks),
            )
            run.usage = usage
            event(
                session,
                run,
                "dispatch.reserved",
                {"execution_id": execution.id, "task_id": execution.task_id, "usage": usage},
                operation,
            )

        return reserve

    async def advance(self, identity):
        with transaction(self.engine) as session:
            run = session.get(AutonomousRun, identity)
            if run is None:
                raise ValueError("Unknown autonomous run")
            if run.current_operation or run.state in {
                "REPORTED",
                "PAUSED",
                "BLOCKED",
                "RECOVERY_REQUIRED",
                "AWAITING_APPROVAL",
            }:
                return report(self.engine, identity)
            self.retain_elapsed(run)
            bounds = run.request["limits"]
            if self.remaining(run) <= 0 or run.usage["steps"] >= bounds["max_steps"]:
                run.state = "PAUSED"
                run.checkpoint = {
                    "category": "budget",
                    "reason": "Elapsed time or workflow-step budget exhausted",
                }
                event(session, run, "checkpoint", run.checkpoint)
                return self._snapshot_after(session, identity)
            request = AutonomousRequest.model_validate(run.request)
            request.publication_grants.update(run.references.get("publication_grants", {}))
            if request.delivery_manifest is None and run.references.get("delivery_manifest"):
                from .delivery_models import Manifest

                request.delivery_manifest = Manifest.model_validate(
                    run.references["delivery_manifest"]
                )
            operation = AutonomousOperation(
                id=str(uuid4()),
                run_id=identity,
                sequence=run.usage["steps"] + 1,
                step=run.step,
                request_hash=run.request_hash,
            )
            session.add(operation)
            session.flush()
            run.current_operation, run.state = operation.id, run.step
            run.usage = {**run.usage, "steps": operation.sequence}
            event(
                session,
                run,
                "operation.intended",
                {"step": run.step, "request_hash": run.request_hash},
                operation.id,
            )
            op_id, step = operation.id, run.step
        self.fault("after-intent", op_id)
        with transaction(self.engine) as session:
            run = session.get(AutonomousRun, identity)
            if run.state == "PAUSED":
                return report(self.engine, identity)
            event(session, run, "operation.dispatched", {"step": step}, op_id)
        try:
            self.fault("before-dispatch", op_id)
            result = await self.services.perform(
                step, request, report(self.engine, identity), self.dispatch_guard(identity, op_id)
            )
            result = StepResult.model_validate(result.model_dump())
            self.fault("after-observation", op_id)
        except BudgetExceeded as exc:
            # A rolled-back scheduler claim proves no dispatch from that transaction.
            return self._finish(
                identity,
                op_id,
                StepResult(next_step=step, checkpoint={"category": "budget", "reason": str(exc)}),
                "PAUSED",
            )
        except BaseException:
            # Persisted intent is retained. Never infer safe retry from an exception.
            checkpoint(
                self.engine,
                identity,
                "RECOVERY_REQUIRED",
                "recovery",
                "Operation outcome is uncertain; reconcile child evidence before continuation",
            )
            raise
        return self._finish(identity, op_id, result)

    @staticmethod
    def _snapshot_after(session, identity):
        session.flush()
        # Commit before opening the read-only presentation session.
        session.commit()
        return report(session.bind, identity)

    def observed_usage(self, session, run):
        reserved = list(
            session.scalars(
                select(AutonomousEvent).where(
                    AutonomousEvent.run_id == run.id, AutonomousEvent.kind == "dispatch.reserved"
                )
            )
        )
        total_input, total_output, known = 0, 0, 0
        for reservation in reserved:
            execution = session.get(Execution, reservation.payload["execution_id"])
            usage = (execution.result or {}).get("usage") if execution else None
            if usage and all(
                isinstance(usage.get(k), int)
                and not isinstance(usage.get(k), bool)
                and usage[k] >= 0
                for k in ("input_tokens", "output_tokens")
            ):
                total_input += usage["input_tokens"]
                total_output += usage["output_tokens"]
                known += 1
        run.usage = {
            **run.usage,
            "known_input_tokens": total_input,
            "known_output_tokens": total_output,
            "usage_observations": known,
            "tokens": total_input + total_output if reserved and known == len(reserved) else None,
        }

    def _finish(self, identity, operation, result, forced_state=None):
        self.fault("before-commit", operation)
        with transaction(self.engine) as session:
            run = session.get(AutonomousRun, identity)
            if run.current_operation != operation:
                raise PermissionError("Operation ownership changed")
            with Session(self.engine) as reader:
                intended = reader.get(AutonomousOperation, operation)
                edges = {
                    "RECONCILING": {"RECONCILING", "PREPARING_DESIGN"},
                    "PREPARING_DESIGN": {"PREPARING_DESIGN", "PLANNING_TASKS", "REPORTED"},
                    "PLANNING_TASKS": {"PLANNING_TASKS", "EXECUTING"},
                    "EXECUTING": {"EXECUTING", "VERIFYING"},
                    "VERIFYING": {"VERIFYING", "EXECUTING", "PREPARING_DELIVERY"},
                    "PREPARING_DELIVERY": {"PREPARING_DELIVERY", "OBSERVING_DELIVERY"},
                    "OBSERVING_DELIVERY": {"OBSERVING_DELIVERY", "REPORTED"},
                }
                if result.next_step not in edges.get(intended.step, set()):
                    raise ValueError("Invalid autonomous state transition")
            paused = run.state == "PAUSED"
            operator_checkpoint = run.checkpoint if paused else None
            self.retain_elapsed(run)
            self.observed_usage(session, run)
            run.current_operation = None
            run.step = result.next_step
            run.checkpoint = operator_checkpoint or result.checkpoint
            category = (result.checkpoint or {}).get("category")
            if category == "budget":
                outcome = "PAUSED"
            elif category == "recovery":
                outcome = "RECOVERY_REQUIRED"
            elif category in {
                "requirements",
                "design",
                "plan",
                "execution",
                "security-policy",
                "delivery-approval",
                "publication",
                "authorization",
            }:
                outcome = "AWAITING_APPROVAL"
            elif result.checkpoint:
                outcome = "BLOCKED"
            else:
                outcome = result.next_step
            run.state = "PAUSED" if paused else forced_state or outcome
            if result.next_step == "REPORTED" and not result.checkpoint:
                run.active_milestone = None
            if self.remaining(run) <= 0 and run.state != "REPORTED":
                run.state = "PAUSED"
                run.checkpoint = {"category": "budget", "reason": "Elapsed run deadline exhausted"}
            event(session, run, "operation.committed", result.model_dump(mode="json"), operation)
        self.fault("after-commit", operation)
        return report(self.engine, identity)

    async def run(self, identity):
        # Every iteration consumes a persisted step. No unbounded polling or advancement.
        for _ in range(self.settings.autonomous_max_steps):
            value = await self.advance(identity)
            if (
                value["state"]
                in {"REPORTED", "AWAITING_APPROVAL", "PAUSED", "BLOCKED", "RECOVERY_REQUIRED"}
                or value["current_operation"]
            ):
                return value
        return checkpoint(
            self.engine, identity, "PAUSED", "budget", "Per-invocation workflow step limit reached"
        )

    def pause(self, identity):
        return checkpoint(
            self.engine,
            identity,
            "PAUSED",
            "operator",
            "Explicit operator pause; active child ownership retained",
        )

    async def resume(self, identity, publication_grants=None, delivery_manifest=None):
        with transaction(self.engine) as session:
            run = session.get(AutonomousRun, identity)
            if run is None:
                raise ValueError("Unknown autonomous run")
            if run.current_operation:
                raise PermissionError("Reconcile unfinished operation before resume")
            if run.state == "REPORTED":
                return report(self.engine, identity)
            references = dict(run.references)
            if publication_grants:
                for key in publication_grants:
                    if key.rsplit(":", 1)[-1] not in {"prepare", "push", "create-pr"}:
                        raise ValueError("Unsupported publication action")
                references["publication_grants"] = {
                    **references.get("publication_grants", {}),
                    **publication_grants,
                }
            if delivery_manifest:
                if (
                    delivery_manifest.milestone != run.milestone
                    or delivery_manifest.project != "agrosphere"
                ):
                    raise ValueError("Delivery manifest changed milestone scope")
                payload = delivery_manifest.model_dump(mode="json")
                prior = run.request.get("delivery_manifest") or references.get("delivery_manifest")
                if prior and prior != payload:
                    raise PermissionError("Registered delivery manifest is immutable")
                references["delivery_manifest"] = payload
            run.references = references
            event(session, run, "references.bound", references)
            run.state, run.checkpoint = run.step, None
            event(session, run, "resumed", {"step": run.step, "usage": run.usage})
        return await self.run(identity)

    async def recover(self, identity):
        value = report(self.engine, identity)
        if not value["current_operation"]:
            return value
        with Session(self.engine) as session:
            op = session.get(AutonomousOperation, value["current_operation"])
            request = AutonomousRequest.model_validate(session.get(AutonomousRun, identity).request)
            run = session.get(AutonomousRun, identity)
            request.publication_grants.update(run.references.get("publication_grants", {}))
            if request.delivery_manifest is None and run.references.get("delivery_manifest"):
                from .delivery_models import Manifest

                request.delivery_manifest = Manifest.model_validate(
                    run.references["delivery_manifest"]
                )
        # This service observes existing child records; it must never redispatch writes.
        result = await self.services.recover(op.step, request, value)
        if result is None:
            return checkpoint(
                self.engine,
                identity,
                "RECOVERY_REQUIRED",
                "recovery",
                "No independently verified child outcome; retain reservations and ownership",
            )
        return self._finish(identity, op.id, result)

    def validate(self, identity):
        value = report(self.engine, identity)
        with Session(self.engine) as session:
            run = session.get(AutonomousRun, identity)
            errors = []
            if digest(canonical(run.request)) != run.request_hash:
                errors.append("Immutable request digest mismatch")
            operations = list(
                session.scalars(
                    select(AutonomousOperation).where(AutonomousOperation.run_id == identity)
                )
            )
            if len(operations) != run.usage["steps"] or len(
                {o.sequence for o in operations}
            ) != len(operations):
                errors.append("Operation sequence or step accounting mismatch")
            for name, limit in (
                ("invocations", "max_invocations"),
                ("attempts", "max_attempts"),
                ("repairs", "max_repairs"),
                ("polls", "max_steps"),
                ("poll_seconds", "max_poll_seconds"),
            ):
                if not 0 <= run.usage[name] <= run.request["limits"][limit]:
                    errors.append("Budget accounting violation: " + name)
            if len(run.usage["tasks"]) > run.request["limits"]["max_tasks"]:
                errors.append("Task budget violation")
            reservations = [e for e in value["events"] if e["kind"] == "dispatch.reserved"]
            if (
                len(reservations) != run.usage["invocations"]
                or run.usage["attempts"] != run.usage["invocations"]
            ):
                errors.append("Dispatch reservation accounting mismatch")
            committed = [
                e["operation_id"] for e in value["events"] if e["kind"] == "operation.committed"
            ]
            if len(committed) != len(set(committed)):
                errors.append("Operation outcome was adopted more than once")
            if errors:
                raise ValueError("; ".join(errors))
        return {
            "valid": True,
            "run_id": identity,
            "state": value["state"],
            "formally_completed": False,
        }
