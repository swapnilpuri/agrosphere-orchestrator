"""Add recovery observations without altering approved foundation records."""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "recovery_snapshots",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("workspace", sa.String(), nullable=False),
        sa.Column("observed_at", sa.String(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
    )

    op.create_table(
        "recovery_heads",
        sa.Column("workspace", sa.String(), primary_key=True),
        sa.Column(
            "snapshot_id", sa.String(), sa.ForeignKey("recovery_snapshots.id"), nullable=False
        ),
    )


def downgrade():
    raise RuntimeError("Recovery history is retained; destructive downgrade is unsupported")
