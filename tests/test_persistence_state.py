import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from agrosphere_orchestrator.models import TaskState
from agrosphere_orchestrator.persistence import AuditEvent, Run, Task, import_plan
from agrosphere_orchestrator.state import record_approval, transition


def test_idempotent_and_conflicting_import(engine, plan):
    ids = import_plan(engine, plan)
    assert import_plan(engine, plan) == ids
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(Task)) == 2
        assert session.scalar(select(func.count()).select_from(AuditEvent)) == 4
    changed = plan.model_copy(deep=True)
    changed.tasks[0].title = "Changed"
    with pytest.raises(ValueError, match="different content"):
        import_plan(engine, changed)


@pytest.mark.parametrize(
    "verb", ["UPDATE audit_events SET actor='changed'", "DELETE FROM audit_events"]
)
def test_append_only_audit(engine, plan, verb):
    import_plan(engine, plan)
    with pytest.raises(IntegrityError, match="append-only"):
        with engine.begin() as connection:
            connection.execute(text(verb))
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(AuditEvent)) == 4


def test_transitions_dependencies_and_history(engine, plan, policy):
    first, second = import_plan(engine, plan)
    with pytest.raises(ValueError, match="unauthorized transition"):
        transition(engine, first, TaskState.SUCCEEDED, "human", policy)
    with pytest.raises(ValueError, match="dependencies"):
        transition(engine, second, TaskState.READY, "human", policy)
    for state in (TaskState.READY, TaskState.RUNNING, TaskState.SUCCEEDED):
        transition(engine, first, state, "human", policy)
    transition(engine, second, TaskState.READY, "human", policy)
    with Session(engine) as session:
        events = list(session.scalars(select(AuditEvent).order_by(AuditEvent.id)))
        assert [e.payload["to"] for e in events if e.kind == "task.transitioned"] == [
            "ready",
            "running",
            "succeeded",
            "ready",
        ]
        run = session.scalar(select(Run))
        assert run.status == "succeeded" and run.finished_at
    with pytest.raises(ValueError):
        transition(engine, first, TaskState.READY, "human", policy)


def test_approval_gate_and_denial(engine, plan, policy):
    plan.tasks[0].operation = "code-write"
    task = import_plan(engine, plan)[0]
    transition(engine, task, TaskState.READY, "human", policy)
    with pytest.raises(PermissionError):
        transition(engine, task, TaskState.RUNNING, "human", policy)
    with pytest.raises(PermissionError):
        record_approval(engine, task, "code-write", "agent", True, policy)
    with pytest.raises(ValueError):
        record_approval(engine, task, "deploy", "human", True, policy)
    record_approval(engine, task, "code-write", "human", True, policy)
    record_approval(engine, task, "code-write", "human", False, policy)
    with pytest.raises(PermissionError):
        transition(engine, task, TaskState.RUNNING, "human", policy)
    record_approval(engine, task, "code-write", "human", True, policy)
    # Operation approval remains necessary but no longer bypasses milestone design approval.
    with pytest.raises(PermissionError, match="approved design"):
        transition(engine, task, TaskState.RUNNING, "human", policy)
    with Session(engine) as session:
        assert session.get(Task, task).state == TaskState.READY
        assert session.scalar(select(Run)) is None


def test_default_deny(policy):
    assert policy.requires("unknown-operation")
    assert policy.requires("code-write")
    assert not policy.requires("inspect")


def test_foreign_keys(engine):
    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO runs (id, task_id, status, created_at) "
                    "VALUES ('x', 'missing', 'running', 'now')"
                )
            )
