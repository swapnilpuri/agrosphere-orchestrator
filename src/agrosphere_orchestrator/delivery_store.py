"""Delivery projections with append-only intent and observation evidence."""

from sqlalchemy import JSON, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .persistence import Base, now


class DeliveryRun(Base):
    __tablename__ = "delivery_runs"
    __table_args__ = (UniqueConstraint("milestone_id"),)
    id: Mapped[str] = mapped_column(String, primary_key=True)
    milestone_id: Mapped[str] = mapped_column(ForeignKey("milestones.id"))
    manifest: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(default=now)


class DeliveryUnit(Base):
    __tablename__ = "delivery_units"
    __table_args__ = (UniqueConstraint("run_id", "external_id"),)
    id: Mapped[str] = mapped_column(String, primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("delivery_runs.id"))
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"))
    external_id: Mapped[str]
    state: Mapped[str] = mapped_column(default="PLANNED")
    pr_id: Mapped[int | None]
    observation: Mapped[str | None]


class DeliveryOperation(Base):
    __tablename__ = "delivery_operations"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    unit_id: Mapped[str] = mapped_column(ForeignKey("delivery_units.id"))
    action: Mapped[str]
    scope: Mapped[dict] = mapped_column(JSON)
    approval_id: Mapped[str]
    principal: Mapped[str]
    created_at: Mapped[str] = mapped_column(default=now)


class DeliveryEvent(Base):
    __tablename__ = "delivery_events"
    __table_args__ = (Index("delivery_events_unit_sequence", "unit_id", "sequence"),)
    sequence: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    unit_id: Mapped[str] = mapped_column(ForeignKey("delivery_units.id"))
    operation_id: Mapped[str | None] = mapped_column(ForeignKey("delivery_operations.id"))
    kind: Mapped[str]
    evidence: Mapped[str] = mapped_column(ForeignKey("validation_evidence.id"))
    created_at: Mapped[str] = mapped_column(default=now)
