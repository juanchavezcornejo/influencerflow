"""Add edit_versions table."""

from alembic import op
import sqlalchemy as sa


revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "edit_versions",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("asset_id", sa.String(36), nullable=False),
        sa.Column("parent_version_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("changes_log_text", sa.Text, nullable=True),
        sa.Column("corrections_applied_json", sa.Text, nullable=True),
        sa.Column("output_path", sa.String(1024), nullable=True),
        sa.Column("user_decision", sa.String(50), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.ForeignKeyConstraint(["parent_version_id"], ["edit_versions.id"]),
        sa.Index("ix_edit_version_asset", "asset_id"),
        sa.Index("ix_edit_version_decision", "user_decision"),
    )


def downgrade() -> None:
    op.drop_table("edit_versions")
