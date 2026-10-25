import json
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import JSON, ForeignKey, String, UniqueConstraint, create_engine, event, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from .models import MilestoneSpec


def now() -> str:
    return datetime.now(UTC).isoformat()


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str]


class Milestone(Base):
    __tablename__ = "milestones"
    __table_args__ = (UniqueConstraint("project_id", "external_id"),)
    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"))
    external_id: Mapped[str]
    spec: Mapped[dict] = mapped_column(JSON)


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (UniqueConstraint("milestone_id", "external_id"),)
    id: Mapped[str] = mapped_column(String, primary_key=True)
    milestone_id: Mapped[str] = mapped_column(ForeignKey("milestones.id"))
    external_id: Mapped[str]
    state: Mapped[str] = mapped_column(default="pending")
    spec: Mapped[dict] = mapped_column(JSON)

    @property
    def quality_state(self):
        from sqlalchemy.orm import object_session

        from .quality_store import TaskQuality

        item = object_session(self).get(TaskQuality, self.id)
        return item.state if item else None

    @quality_state.setter
    def quality_state(self, state):
        from sqlalchemy.orm import object_session

        from .quality_store import TaskQuality

        session = object_session(self)
        item = session.get(TaskQuality, self.id)
        if item is None:
            session.add(TaskQuality(task_id=self.id, state=state))
        else:
            item.state = state


class Run(Base):
    __tablename__ = "runs"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"))
    status: Mapped[str]
    created_at: Mapped[str] = mapped_column(default=now)
    finished_at: Mapped[str | None]


class Approval(Base):
    __tablename__ = "approvals"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"))
    operation: Mapped[str]
    decision: Mapped[str]
    actor: Mapped[str]
    created_at: Mapped[str] = mapped_column(default=now)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    entity_id: Mapped[str]
    kind: Mapped[str]
    actor: Mapped[str]
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(default=now)


def make_engine(url: str) -> Engine:
    if not url.startswith("sqlite:"):
        raise ValueError("AEO-1 supports SQLite only")
    engine = create_engine(url)

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")

    return engine


def install_audit_guards(connection) -> None:
    for operation in ("UPDATE", "DELETE"):
        connection.exec_driver_sql(
            f"CREATE TRIGGER IF NOT EXISTS audit_no_{operation.lower()} "
            f"BEFORE {operation} ON audit_events BEGIN "
            "SELECT RAISE(ABORT, 'audit events are append-only'); END"
        )


def audit(session: Session, entity: str, kind: str, actor: str, payload: dict) -> None:
    session.add(AuditEvent(entity_id=entity, kind=kind, actor=actor, payload=payload))


def import_plan(engine: Engine, spec: MilestoneSpec, actor: str = "local-user") -> list[str]:
    """Atomic, repeatable import. Changed content under an existing ID is a conflict.

    Single-writer foundation: no scheduling or concurrent execution in AEO-1.
    """
    payload = spec.model_dump(mode="json")
    with Session(engine) as session, session.begin():
        project = session.get(Project, spec.project)
        if project is None:
            project = Project(id=spec.project, title=spec.project)
            session.add(project)
            session.flush()
            audit(session, project.id, "project.created", actor, {})
        milestone = session.scalar(
            select(Milestone).where(
                Milestone.project_id == spec.project, Milestone.external_id == spec.id
            )
        )
        if milestone is not None:
            if json.dumps(milestone.spec, sort_keys=True) != json.dumps(payload, sort_keys=True):
                raise ValueError("milestone ID already exists with different content")
            return list(
                session.scalars(
                    select(Task.id)
                    .where(Task.milestone_id == milestone.id)
                    .order_by(Task.external_id)
                )
            )
        milestone = Milestone(
            id=str(uuid4()), project_id=project.id, external_id=spec.id, spec=payload
        )
        session.add(milestone)
        session.flush()
        audit(session, milestone.id, "milestone.created", actor, payload)
        ids = []
        for task in sorted(spec.tasks, key=lambda item: item.id):
            record = Task(
                id=str(uuid4()),
                milestone_id=milestone.id,
                external_id=task.id,
                spec=task.model_dump(mode="json"),
                state="pending",
            )
            session.add(record)
            ids.append(record.id)
            audit(session, record.id, "task.created", actor, record.spec)
        return ids


class RecoveryRecord(Base):
    """Content-addressed observations; never updates plan or approval tables."""

    __tablename__ = "recovery_snapshots"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    workspace: Mapped[str]
    observed_at: Mapped[str]
    payload: Mapped[dict] = mapped_column(JSON)


class RecoveryHead(Base):
    __tablename__ = "recovery_heads"
    workspace: Mapped[str] = mapped_column(String, primary_key=True)
    snapshot_id: Mapped[str] = mapped_column(ForeignKey("recovery_snapshots.id"))


class DesignCase(Base):
    __tablename__ = "design_cases"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str]
    external_id: Mapped[str]
    state: Mapped[str] = mapped_column(default="DISCOVERED")
    scope_id: Mapped[str | None]
    revision_id: Mapped[str | None]
    validation_id: Mapped[str | None]


class DesignScope(Base):
    __tablename__ = "design_scopes"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("design_cases.id"))
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(default=now)


class DesignRevision(Base):
    __tablename__ = "design_revisions"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("design_cases.id"))
    scope_id: Mapped[str] = mapped_column(ForeignKey("design_scopes.id"))
    phase: Mapped[str]
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(default=now)


class DesignValidation(Base):
    __tablename__ = "design_validations"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    revision_id: Mapped[str] = mapped_column(ForeignKey("design_revisions.id"))
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(default=now)


class DesignDecision(Base):
    __tablename__ = "design_decisions"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("design_cases.id"))
    subject: Mapped[str]
    kind: Mapped[str]
    decision: Mapped[str]
    actor: Mapped[str]
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(default=now)


class Execution(Base):
    __tablename__ = "executions"
    __table_args__ = (UniqueConstraint("active_slot"),)
    id: Mapped[str] = mapped_column(String, primary_key=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"))
    state: Mapped[str]
    active_slot: Mapped[int | None]
    request: Mapped[dict] = mapped_column(JSON)
    context: Mapped[dict] = mapped_column(JSON)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    session_id: Mapped[str | None]
    cancel_requested: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[str] = mapped_column(default=now)
    updated_at: Mapped[str] = mapped_column(default=now)


class ExecutionGrant(Base):
    __tablename__ = "execution_grants"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    execution_id: Mapped[str] = mapped_column(ForeignKey("executions.id"))
    request_digest: Mapped[str]
    actor: Mapped[str]
    expires_at: Mapped[str]
    created_at: Mapped[str] = mapped_column(default=now)


class ExecutionAttempt(Base):
    __tablename__ = "execution_attempts"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    execution_id: Mapped[str] = mapped_column(ForeignKey("executions.id"))
    state: Mapped[str]
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(default=now)
