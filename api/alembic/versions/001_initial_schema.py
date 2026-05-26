"""Initial schema: users, storage_credentials, sessions, assets.

Revision ID: 001
Revises:
Create Date: 2026-04-16 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial tables."""
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_created_at", "users", ["created_at"])

    op.create_table(
        "storage_credentials",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("refresh_token", sa.Text, nullable=False),
        sa.Column("access_token", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.UniqueConstraint("user_id", "provider", name="uq_storage_user_provider"),
    )
    op.create_index("ix_storage_credentials_user_id", "storage_credentials", ["user_id"])
    op.create_index("ix_storage_credentials_provider", "storage_credentials", ["provider"])
    op.create_index("ix_storage_credentials_created_at", "storage_credentials", ["created_at"])

    op.create_table(
        "sessions",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("cloud_provider", sa.String(50), nullable=False),
        sa.Column("cloud_folder_id", sa.String(255), nullable=False),
        sa.Column("cloud_folder_name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])
    op.create_index("ix_sessions_status", "sessions", ["status"])
    op.create_index("ix_sessions_created_at", "sessions", ["created_at"])

    op.create_table(
        "assets",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("session_id", sa.String(36), nullable=False),
        sa.Column("original_cloud_path", sa.String(1024), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("preview_path", sa.String(1024), nullable=True),
        sa.Column("thumbnail_path", sa.String(1024), nullable=True),
        sa.Column("full_res_local_path", sa.String(1024), nullable=True),
        sa.Column("exif_json", sa.Text, nullable=True),
        sa.Column("gps_lat", sa.Float, nullable=True),
        sa.Column("gps_lng", sa.Float, nullable=True),
        sa.Column("taken_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_video", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("has_face", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("aesthetic_score", sa.Float, nullable=True),
        sa.Column("phash", sa.String(16), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"]),
    )
    op.create_index("ix_assets_session_id", "assets", ["session_id"])
    op.create_index("ix_assets_gps_lat", "assets", ["gps_lat"])
    op.create_index("ix_assets_gps_lng", "assets", ["gps_lng"])
    op.create_index("ix_assets_taken_at", "assets", ["taken_at"])
    op.create_index("ix_assets_phash", "assets", ["phash"])
    op.create_index("ix_asset_session_taken", "assets", ["session_id", "taken_at"])
    op.create_index("ix_asset_session_phash", "assets", ["session_id", "phash"])
    op.create_index("ix_assets_created_at", "assets", ["created_at"])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table("assets")
    op.drop_table("sessions")
    op.drop_table("storage_credentials")
    op.drop_table("users")
