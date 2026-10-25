"""Bounded execution records, immutable grants and attempt evidence."""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "executions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("task_id", sa.String(), sa.ForeignKey("tasks.id"), nullable=False),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("active_slot", sa.Integer()),
        sa.UniqueConstraint("active_slot"),
        sa.Column("request", sa.JSON(), nullable=False),
        sa.Column("context", sa.JSON(), nullable=False),
        sa.Column("result", sa.JSON()),
        sa.Column("session_id", sa.String()),
        sa.Column("cancel_requested", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.Column("updated_at", sa.String(), nullable=False),
    )
    op.create_table(
        "execution_grants",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("execution_id", sa.String(), sa.ForeignKey("executions.id"), nullable=False),
        sa.Column("request_digest", sa.String(), nullable=False),
        sa.Column("actor", sa.String(), nullable=False),
        sa.Column("expires_at", sa.String(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
    )
    op.create_table(
        "execution_attempts",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("execution_id", sa.String(), sa.ForeignKey("executions.id"), nullable=False),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
    )
    for table in ("execution_grants", "execution_attempts"):
        for operation in ("UPDATE", "DELETE"):
            op.execute(
                f"CREATE TRIGGER {table}_no_{operation.lower()} BEFORE {operation} ON {table} "
                "BEGIN SELECT RAISE(ABORT, 'execution history is append-only'); END"
            )


def downgrade():
    raise RuntimeError("Execution history is retained; destructive downgrade unsupported")
