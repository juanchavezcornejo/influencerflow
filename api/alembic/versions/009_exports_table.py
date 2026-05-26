"""Add exports table for tracking ZIP export jobs."""

from alembic import op
import sqlalchemy as sa


revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "exports",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("session_id", sa.String(36), nullable=False),
        sa.Column("group_id", sa.String(36), nullable=False),
        sa.Column("zip_path", sa.String(500), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"]),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"]),
        sa.Index("ix_export_session", "session_id"),
        sa.Index("ix_export_group", "group_id"),
        sa.Index("ix_export_status", "status"),
    )


def downgrade() -> None:
    op.drop_table("exports")
