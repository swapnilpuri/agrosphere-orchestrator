"""Durable run projections and immutable operation/event evidence in the existing DB."""

import json
from uuid import uuid4

from sqlalchemy import JSON, ForeignKey, String, UniqueConstraint, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from .orchestration_store import transaction
from .persistence import Base, audit, now


class AutonomousRun(Base):
    __tablename__ = "autonomous_runs"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    milestone: Mapped[str]
    request_hash: Mapped[str]
    request: Mapped[dict] = mapped_column(JSON)
    state: Mapped[str]
    step: Mapped[str]
    current_operation: Mapped[str | None]
    checkpoint: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    references: Mapped[dict] = mapped_column(JSON, default=dict)
    usage: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(default=now)
    updated_at: Mapped[str] = mapped_column(default=now)
    # Unique slot is retained until REPORTED; expiry never releases uncertainty.
    active_milestone: Mapped[str | None] = mapped_column(unique=True, nullable=True)


class AutonomousOperation(Base):
    __tablename__ = "autonomous_operations"
    __table_args__ = (UniqueConstraint("run_id", "sequence"),)
    id: Mapped[str] = mapped_column(String, primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("autonomous_runs.id"))
    sequence: Mapped[int]
    step: Mapped[str]
    request_hash: Mapped[str]
    created_at: Mapped[str] = mapped_column(default=now)


class AutonomousEvent(Base):
    __tablename__ = "autonomous_events"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("autonomous_runs.id"))
    operation_id: Mapped[str | None] = mapped_column(ForeignKey("autonomous_operations.id"))
    kind: Mapped[str]
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(default=now)


def event(session, run, kind, payload, operation=None):
    session.add(
        AutonomousEvent(
            id=str(uuid4()), run_id=run.id, operation_id=operation, kind=kind, payload=payload
        )
    )
    run.updated_at = now()
    audit(session, run.id, "autonomous." + kind, "autonomous-controller", payload)


def report(engine, identity):
    with Session(engine) as session:
        run = session.get(AutonomousRun, identity)
        if run is None:
            raise ValueError("Unknown autonomous run")
        records = list(
            session.scalars(
                select(AutonomousEvent)
                .where(AutonomousEvent.run_id == identity)
                .order_by(AutonomousEvent.created_at, AutonomousEvent.id)
            )
        )
        return {
            "run_id": run.id,
            "milestone": run.milestone,
            "mode": run.request["mode"],
            "state": run.state,
            "step": run.step,
            "checkpoint": run.checkpoint,
            "request_hash": run.request_hash,
            "limits": run.request["limits"],
            "usage": run.usage,
            "references": run.references,
            "current_operation": run.current_operation,
            "created_at": run.created_at,
            "updated_at": run.updated_at,
            "formally_completed": False,
            "freshness": "Persisted observations; continuation rechecks current authority and artifacts. REPORTED is not formal completion.",
            "events": [
                {
                    "id": r.id,
                    "kind": r.kind,
                    "operation_id": r.operation_id,
                    "payload": r.payload,
                    "created_at": r.created_at,
                }
                for r in records
            ],
        }


def checkpoint(engine, identity, state, category, reason, command=None):
    with transaction(engine) as session:
        run = session.get(AutonomousRun, identity)
        if run is None:
            raise ValueError("Unknown autonomous run")
        run.state = state
        run.checkpoint = {"category": category, "reason": reason, "command": command}
        event(session, run, "checkpoint", run.checkpoint, run.current_operation)
    return report(engine, identity)


def markdown(value):
    lines = [
        "# Autonomous run " + value["run_id"],
        "",
        "Milestone: " + value["milestone"],
        "State: " + value["state"],
        "Step: " + value["step"],
        "Formal milestone completion: false",
        "",
        "## Usage",
        "",
        "~~~json",
        json.dumps(value["usage"], indent=2),
        "~~~",
        "",
        "## Checkpoint",
        "",
        "~~~json",
        json.dumps(value["checkpoint"], indent=2),
        "~~~",
        "",
        "## Evidence",
        "",
    ]
    for item in value["events"]:
        lines.extend(
            ["### " + item["kind"], "", "~~~json", json.dumps(item["payload"], indent=2), "~~~", ""]
        )
    return "\n".join(lines) + "\n"


def export_report(engine, identity, directory):
    """Publish immutable reports atomically; interrupted exports can be retried from DB."""
    import os
    import tempfile
    from pathlib import Path

    from .design import canonical
    from .design_artifacts import digest

    value = report(engine, identity)
    directory = Path(directory)
    if any(p.is_symlink() for p in (directory, *directory.parents)):
        raise ValueError("Report directory cannot traverse symlinks")
    base = directory.resolve()
    destination = base / digest(identity)
    destination.mkdir(parents=True, exist_ok=True)
    if destination.is_symlink() or not destination.resolve().is_relative_to(base):
        raise ValueError("Report destination escaped configured root")
    hashed = digest(canonical(value))
    outputs = {
        hashed + ".json": json.dumps(value, indent=2) + "\n",
        hashed + ".md": markdown(value),
    }
    for name, content in outputs.items():
        target = destination / name
        if target.is_symlink():
            raise ValueError("Report file cannot be a symlink")
        if target.exists():
            if target.read_bytes() != content.encode("utf-8"):
                raise ValueError("Immutable report content changed")
            continue
        with tempfile.NamedTemporaryFile(dir=destination, delete=False) as temporary:
            temporary.write(content.encode("utf-8"))
            temporary.flush()
            os.fsync(temporary.fileno())
            source = Path(temporary.name)
        try:
            try:
                os.link(source, target)
            except FileExistsError:
                if target.read_bytes() != content.encode("utf-8"):
                    raise ValueError("Immutable report changed during publication") from None
        finally:
            source.unlink(missing_ok=True)
    return {"report_hash": hashed, "files": [str(destination / name) for name in outputs]}
