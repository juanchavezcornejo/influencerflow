"""Add face_crops table for face retouch workflow."""

from alembic import op
import sqlalchemy as sa


revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "face_crops",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("asset_id", sa.String(36), nullable=False),
        sa.Column("bbox_json", sa.Text, nullable=False),
        sa.Column("landmarks_json", sa.Text, nullable=True),
        sa.Column("crop_path", sa.String(1024), nullable=False),
        sa.Column("user_uploaded_path", sa.String(1024), nullable=True),
        sa.Column("blended_output_path", sa.String(1024), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, default="cropped"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.Index("ix_face_crop_asset", "asset_id"),
        sa.Index("ix_face_crop_status", "status"),
    )


def downgrade() -> None:
    op.drop_table("face_crops")
