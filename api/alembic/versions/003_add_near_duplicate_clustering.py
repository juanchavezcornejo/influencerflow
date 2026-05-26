"""Add near_duplicate_cluster_id to assets table."""

from alembic import op
import sqlalchemy as sa


revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "assets",
        sa.Column("near_duplicate_cluster_id", sa.String(36), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("assets", "near_duplicate_cluster_id")
