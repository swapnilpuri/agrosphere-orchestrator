"""Append-only governance events and content-addressed evidence in the existing DB."""

import hashlib
import json
from uuid import uuid4

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .persistence import Base, audit, now


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


class GovernanceRecord(Base):
    __tablename__ = "governance_records"
    sequence: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id: Mapped[str] = mapped_column(String, unique=True)
    milestone_id: Mapped[str] = mapped_column(ForeignKey("milestones.id"))
    task_id: Mapped[str | None] = mapped_column(ForeignKey("tasks.id"))
    kind: Mapped[str]
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(default=now)


class EvidenceBlob(Base):
    __tablename__ = "validation_evidence"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(default=now)


def record(session, milestone, kind, payload, actor="quality-engine", task=None):
    item = GovernanceRecord(
        id=str(uuid4()), milestone_id=milestone, task_id=task, kind=kind, payload=payload
    )
    session.add(item)
    audit(
        session, task or milestone, "governance." + kind, actor, {"record_id": item.id, **payload}
    )
    session.flush()
    return item.id


def blob(session, payload):
    identity = digest(payload)
    if session.get(EvidenceBlob, identity) is None:
        session.add(EvidenceBlob(id=identity, payload=payload))
        session.flush()
    return identity


def read_blob(session, identity):
    value = session.get(EvidenceBlob, identity)
    if value is None or digest(value.payload) != identity:
        raise PermissionError("Missing or corrupted validation evidence")
    return value.payload


class TaskQuality(Base):
    """Mutable projection; every change is paired with append-only governance evidence."""

    __tablename__ = "task_quality_states"
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), primary_key=True)
    state: Mapped[str]
