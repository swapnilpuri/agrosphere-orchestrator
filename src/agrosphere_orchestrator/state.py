from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from .configuration import ApprovalPolicy
from .models import TaskState
from .persistence import Approval, Milestone, Run, Task, audit, now

TRANSITIONS = {
    TaskState.PENDING: {TaskState.READY, TaskState.CANCELLED},
    TaskState.READY: {TaskState.RUNNING, TaskState.CANCELLED},
    TaskState.RUNNING: {TaskState.SUCCEEDED, TaskState.FAILED, TaskState.CANCELLED},
    TaskState.FAILED: {TaskState.READY, TaskState.CANCELLED},
    TaskState.SUCCEEDED: set(),
    TaskState.CANCELLED: set(),
}


def record_approval(
    engine: Engine, task_id: str, operation: str, actor: str, approved: bool, policy: ApprovalPolicy
) -> str:
    if actor not in policy.approvers:
        raise PermissionError("actor is not an authorized approver")
    with Session(engine) as session, session.begin():
        task = session.get(Task, task_id)
        if task is None:
            raise ValueError("unknown task")
        if operation != task.spec["operation"]:
            raise ValueError("approval operation does not match task")
        record = Approval(
            id=str(uuid4()),
            task_id=task_id,
            operation=operation,
            actor=actor,
            decision="approved" if approved else "denied",
        )
        session.add(record)
        audit(
            session,
            task_id,
            "approval.recorded",
            actor,
            {"approval_id": record.id, "operation": operation, "decision": record.decision},
        )
        return record.id


def transition(
    engine: Engine, task_id: str, target: TaskState, actor: str, policy: ApprovalPolicy
) -> None:
    target = TaskState(target)
    with Session(engine) as session, session.begin():
        task = session.get(Task, task_id)
        if task is None:
            raise ValueError("unknown task")
        source = TaskState(task.state)
        if target not in TRANSITIONS[source]:
            raise ValueError(f"unauthorized transition: {source} -> {target}")
        if target in {TaskState.READY, TaskState.RUNNING}:
            siblings = {
                item.external_id: item
                for item in session.scalars(
                    select(Task).where(Task.milestone_id == task.milestone_id)
                )
            }
            if any(siblings[dep].state != TaskState.SUCCEEDED for dep in task.spec["depends_on"]):
                raise ValueError("dependencies have not succeeded")
        if target == TaskState.RUNNING and policy.requires(task.spec["operation"]):
            decisions = list(
                session.scalars(
                    select(Approval)
                    .where(
                        Approval.task_id == task_id, Approval.operation == task.spec["operation"]
                    )
                    .order_by(Approval.created_at, Approval.id)
                )
            )
            if not decisions or decisions[-1].decision != "approved":
                raise PermissionError("operation requires approval")
            if decisions[-1].actor not in policy.approvers:
                raise PermissionError("approver no longer authorized")
        if target == TaskState.RUNNING and task.spec["operation"] not in {
            "plan",
            "inspect",
            "validate",
        }:
            from .design import assert_design_gate, move
            from .design_models import MilestoneState

            milestone = session.get(Milestone, task.milestone_id)
            case = assert_design_gate(session, milestone)
            if case.state == MilestoneState.IMPLEMENTATION_READY:
                move(session, case, MilestoneState.IMPLEMENTING, actor)
        task.state = target.value
        if target == TaskState.RUNNING:
            run = Run(id=str(uuid4()), task_id=task_id, status="running")
            session.add(run)
            audit(session, run.id, "run.created", actor, {"task_id": task_id})
        if source == TaskState.RUNNING:
            run = session.scalar(select(Run).where(Run.task_id == task_id, Run.status == "running"))
            if run is None:
                raise ValueError("running task has no active run")
            run.status = target.value
            run.finished_at = now()
            audit(session, run.id, "run.finished", actor, {"status": target.value})
        audit(
            session, task_id, "task.transitioned", actor, {"from": source.value, "to": target.value}
        )
