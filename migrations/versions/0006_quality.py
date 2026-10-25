"""Independent quality evidence and additive task governance lifecycle."""

from alembic import op

from agrosphere_orchestrator.quality_store import EvidenceBlob, GovernanceRecord, TaskQuality

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade():
    TaskQuality.__table__.create(op.get_bind())
    for model in (EvidenceBlob, GovernanceRecord):
        model.__table__.create(op.get_bind())
        for operation in ("UPDATE", "DELETE"):
            op.execute(
                f"CREATE TRIGGER {model.__tablename__}_no_{operation.lower()} BEFORE {operation} ON {model.__tablename__} BEGIN SELECT RAISE(ABORT, 'governance evidence is append-only'); END"
            )


def downgrade():
    raise RuntimeError("Validation and approval history must be retained")
