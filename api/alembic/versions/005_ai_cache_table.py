"""Add ai_cache table for API response caching."""

from alembic import op
import sqlalchemy as sa


revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_cache",
        sa.Column("cache_key", sa.String(64), nullable=False),
        sa.Column("response_json", sa.Text, nullable=False),
        sa.Column("model_used", sa.String(100), nullable=True),
        sa.Column("tokens_in", sa.Integer, nullable=True),
        sa.Column("tokens_out", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("cache_key"),
        sa.Index("ix_cache_created", "created_at"),
    )


def downgrade() -> None:
    op.drop_table("ai_cache")
