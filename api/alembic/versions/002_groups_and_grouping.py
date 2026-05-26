"""Add groups and group_assets tables for photo grouping.

Revision ID: 002
Revises: 001
Create Date: 2026-04-16 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create groups and group_assets tables."""
    op.create_table(
        "groups",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("session_id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("auto_generated", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("order_index", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"]),
    )
    op.create_index("ix_groups_session_id", "groups", ["session_id"])
    op.create_index("ix_groups_order_index", "groups", ["order_index"])

    op.create_table(
        "group_assets",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("group_id", sa.String(36), nullable=False),
        sa.Column("asset_id", sa.String(36), nullable=False),
        sa.Column("position", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"]),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.UniqueConstraint("group_id", "asset_id", name="uq_group_asset"),
    )
    op.create_index("ix_group_assets_group_id", "group_assets", ["group_id"])
    op.create_index("ix_group_assets_asset_id", "group_assets", ["asset_id"])
    op.create_index("ix_group_assets_position", "group_assets", ["position"])


def downgrade() -> None:
    """Drop groups and group_assets tables."""
    op.drop_table("group_assets")
    op.drop_table("groups")
