"""Versioned plans, claims, resource leases and immutable orchestration evidence."""

from alembic import op

from agrosphere_orchestrator.orchestration_store import (
    OrchestrationControl,
    OrchestrationEvidence,
    PlanRevision,
    ResourceLease,
    TaskClaim,
)

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    for model in (
        PlanRevision,
        OrchestrationControl,
        TaskClaim,
        ResourceLease,
        OrchestrationEvidence,
    ):
        model.__table__.create(op.get_bind())
    for table in ("orchestration_plans", "orchestration_evidence"):
        for operation in ("UPDATE", "DELETE"):
            op.execute(
                f"CREATE TRIGGER {table}_no_{operation.lower()} "
                f"BEFORE {operation} ON {table} BEGIN "
                "SELECT RAISE(ABORT, 'orchestration history is append-only'); END"
            )


def downgrade():
    raise RuntimeError("Orchestration evidence is retained; destructive downgrade unsupported")
