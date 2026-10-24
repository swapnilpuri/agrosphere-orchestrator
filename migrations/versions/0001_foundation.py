"""Foundation schema and append-only audit guards."""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "projects",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("title", sa.String(), nullable=False),
    )
    op.create_table(
        "milestones",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("external_id", sa.String(), nullable=False),
        sa.Column("spec", sa.JSON(), nullable=False),
        sa.UniqueConstraint("project_id", "external_id"),
    )
    op.create_table(
        "tasks",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("milestone_id", sa.String(), sa.ForeignKey("milestones.id"), nullable=False),
        sa.Column("external_id", sa.String(), nullable=False),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("spec", sa.JSON(), nullable=False),
        sa.UniqueConstraint("milestone_id", "external_id"),
    )
    op.create_table(
        "runs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("task_id", sa.String(), sa.ForeignKey("tasks.id"), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.Column("finished_at", sa.String()),
    )
    op.create_table(
        "approvals",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("task_id", sa.String(), sa.ForeignKey("tasks.id"), nullable=False),
        sa.Column("operation", sa.String(), nullable=False),
        sa.Column("decision", sa.String(), nullable=False),
        sa.Column("actor", sa.String(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
    )
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("entity_id", sa.String(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("actor", sa.String(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
    )
    for operation in ("UPDATE", "DELETE"):
        op.execute(
            f"CREATE TRIGGER audit_no_{operation.lower()} BEFORE {operation} "
            "ON audit_events BEGIN SELECT RAISE(ABORT, 'audit events are append-only'); END"
        )


def downgrade():
    raise RuntimeError("AEO-1 does not support destructive audit-history downgrades")
