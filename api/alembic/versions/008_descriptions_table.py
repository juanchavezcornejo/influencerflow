"""Add descriptions table for group captions."""

from alembic import op
import sqlalchemy as sa


revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "descriptions",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("group_id", sa.String(36), nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("custom_prompt", sa.Text, nullable=True),
        sa.Column("model_used", sa.String(100), nullable=True),
        sa.Column("tokens_in", sa.Integer, nullable=True),
        sa.Column("tokens_out", sa.Integer, nullable=True),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"]),
        sa.Index("ix_desc_group", "group_id"),
        sa.Index("ix_desc_current", "group_id", "is_current"),
    )


def downgrade() -> None:
    op.drop_table("descriptions")
