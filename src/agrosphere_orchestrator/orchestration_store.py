"""SQLite single-host coordination, using the existing metadata and audit transaction."""

from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import JSON, ForeignKey, String, select, text
from sqlalchemy.orm import Mapped, Session, mapped_column

from .persistence import Base, audit, now


class PlanRevision(Base):
    __tablename__ = "orchestration_plans"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    milestone_id: Mapped[str] = mapped_column(ForeignKey("milestones.id"))
    version: Mapped[int]
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(default=now)


class OrchestrationControl(Base):
    __tablename__ = "orchestration_controls"
    milestone_id: Mapped[str] = mapped_column(ForeignKey("milestones.id"), primary_key=True)
    plan_id: Mapped[str] = mapped_column(ForeignKey("orchestration_plans.id"))
    paused: Mapped[bool] = mapped_column(default=False)


class TaskClaim(Base):
    __tablename__ = "task_claims"
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), primary_key=True)
    owner: Mapped[str]
    execution_id: Mapped[str | None] = mapped_column(ForeignKey("executions.id"))
    expires_at: Mapped[str]
    reconciliation_required: Mapped[bool] = mapped_column(default=False)


class ResourceLease(Base):
    __tablename__ = "resource_leases"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    resource: Mapped[str]
    owner: Mapped[str]
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"))
    write: Mapped[bool]
    expires_at: Mapped[str]


class OrchestrationEvidence(Base):
    __tablename__ = "orchestration_evidence"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    milestone_id: Mapped[str] = mapped_column(ForeignKey("milestones.id"))
    task_id: Mapped[str | None] = mapped_column(ForeignKey("tasks.id"))
    kind: Mapped[str]
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(default=now)


@contextmanager
def transaction(engine):
    # Serialize read-check-write across local processes. Never await inside this boundary.
    with Session(engine) as session:
        session.execute(text("BEGIN IMMEDIATE"))
        try:
            yield session
            session.commit()
        except BaseException:
            session.rollback()
            raise


def evidence(session, milestone, task, kind, payload, identity=None):
    identity = identity or str(uuid4())
    existing = session.get(OrchestrationEvidence, identity)
    if existing:
        if existing.payload != payload or existing.kind != kind:
            raise ValueError("Idempotency key reused with different evidence")
        return identity
    session.add(
        OrchestrationEvidence(
            id=identity, milestone_id=milestone, task_id=task, kind=kind, payload=payload
        )
    )
    audit(session, task or milestone, "orchestration." + kind, "scheduler", payload)
    return identity


def expiry(seconds):
    return (datetime.now(UTC) + timedelta(seconds=seconds)).isoformat()


def acquire(session, task_id, owner, resources, write, seconds):
    leases = list(session.scalars(select(ResourceLease)))
    # Expiry is uncertainty, never permission to steal a write lease.
    for resource in sorted(set(resources)):
        if any(lease.resource == resource and (write or lease.write) for lease in leases):
            return False
    for resource in sorted(set(resources)):
        session.add(
            ResourceLease(
                id=str(uuid4()),
                resource=resource,
                owner=owner,
                task_id=task_id,
                write=write,
                expires_at=expiry(seconds),
            )
        )
    return True


def release(session, owner):
    for lease in session.scalars(select(ResourceLease).where(ResourceLease.owner == owner)):
        session.delete(lease)
