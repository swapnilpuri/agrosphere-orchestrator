"""Durable delivery manifests, intents, and append-only observation history."""

from alembic import op

from agrosphere_orchestrator.delivery_store import (
    DeliveryEvent,
    DeliveryOperation,
    DeliveryRun,
    DeliveryUnit,
)

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade():
    for model in (DeliveryRun, DeliveryUnit, DeliveryOperation, DeliveryEvent):
        model.__table__.create(op.get_bind())
        if model is not DeliveryUnit:
            for operation in ("UPDATE", "DELETE"):
                op.execute(
                    f"CREATE TRIGGER {model.__tablename__}_no_{operation.lower()} BEFORE {operation} ON {model.__tablename__} BEGIN SELECT RAISE(ABORT, 'delivery history is append-only'); END"
                )
    op.execute(
        "CREATE TRIGGER delivery_units_no_delete BEFORE DELETE ON delivery_units BEGIN SELECT RAISE(ABORT, 'delivery units must be retained'); END"
    )
    op.execute(
        "CREATE TRIGGER delivery_units_identity BEFORE UPDATE OF id, run_id, task_id, external_id ON delivery_units BEGIN SELECT RAISE(ABORT, 'delivery identity is immutable'); END"
    )
    op.execute(
        "CREATE TRIGGER delivery_units_pr_identity BEFORE UPDATE OF pr_id ON delivery_units WHEN OLD.pr_id IS NOT NULL AND NEW.pr_id IS NOT OLD.pr_id BEGIN SELECT RAISE(ABORT, 'PR identity is immutable'); END"
    )


def downgrade():
    raise RuntimeError("Delivery and approval history must be retained")
