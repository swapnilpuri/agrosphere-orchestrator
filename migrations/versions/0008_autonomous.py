"""Add bounded autonomous runs without changing existing state or approval tables."""

from alembic import op

from agrosphere_orchestrator.autonomous_store import (
    AutonomousEvent,
    AutonomousOperation,
    AutonomousRun,
)

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade():
    for model in (AutonomousRun, AutonomousOperation, AutonomousEvent):
        model.__table__.create(op.get_bind())
        for operation in ("DELETE",) if model is AutonomousRun else ("UPDATE", "DELETE"):
            op.execute(
                f"CREATE TRIGGER {model.__tablename__}_no_{operation.lower()} BEFORE {operation} ON {model.__tablename__} BEGIN SELECT RAISE(ABORT, 'autonomous history must be retained'); END"
            )
    op.execute(
        "CREATE TRIGGER autonomous_runs_identity BEFORE UPDATE OF id, milestone, request_hash, request, created_at ON autonomous_runs BEGIN SELECT RAISE(ABORT, 'autonomous run identity is immutable'); END"
    )


def downgrade():
    raise RuntimeError("Autonomous intent, budgets and audit history must be retained")
