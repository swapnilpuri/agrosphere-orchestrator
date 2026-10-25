"""Add documentation lifecycle alongside unchanged foundation and recovery state."""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "design_cases",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("external_id", sa.String(), nullable=False),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("scope_id", sa.String()),
        sa.Column("revision_id", sa.String()),
        sa.Column("validation_id", sa.String()),
    )
    op.create_table(
        "design_scopes",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("case_id", sa.String(), sa.ForeignKey("design_cases.id"), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
    )
    op.create_table(
        "design_revisions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("case_id", sa.String(), sa.ForeignKey("design_cases.id"), nullable=False),
        sa.Column("scope_id", sa.String(), sa.ForeignKey("design_scopes.id"), nullable=False),
        sa.Column("phase", sa.String(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
    )
    op.create_table(
        "design_validations",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("revision_id", sa.String(), sa.ForeignKey("design_revisions.id"), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
    )
    op.create_table(
        "design_decisions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("case_id", sa.String(), sa.ForeignKey("design_cases.id"), nullable=False),
        sa.Column("subject", sa.String(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("decision", sa.String(), nullable=False),
        sa.Column("actor", sa.String(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
    )
    for table in ("design_scopes", "design_revisions", "design_validations", "design_decisions"):
        for operation in ("UPDATE", "DELETE"):
            op.execute(
                f"CREATE TRIGGER {table}_no_{operation.lower()} BEFORE {operation} ON {table} "
                "BEGIN SELECT RAISE(ABORT, 'design history is append-only'); END"
            )


def downgrade():
    raise RuntimeError("Design/approval history is retained; destructive downgrade is unsupported")
