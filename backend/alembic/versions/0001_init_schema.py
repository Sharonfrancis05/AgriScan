"""init schema: diseases_reference, scans, reports

Revision ID: 0001
Revises:
Create Date: 2026-08-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SEVERITY_LEVELS = ("Healthy", "Mild", "Moderate", "Severe", "Critical")


def upgrade() -> None:
    op.create_table(
        "diseases_reference",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("crop", sa.String(50), nullable=False),
        sa.Column("disease_code", sa.String(100), nullable=False, unique=True),
        sa.Column("disease_display_name", sa.String(150), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("treatment_text", sa.Text, nullable=True),
        sa.Column("prevention_text", sa.Text, nullable=True),
        sa.Column("is_healthy_label", sa.Boolean, nullable=False, server_default=sa.false()),
    )

    op.create_table(
        "scans",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("scan_uuid", sa.String(36), nullable=False, unique=True),
        sa.Column("user_id", sa.Integer, nullable=True),
        sa.Column("original_image_path", sa.String(500), nullable=False),
        sa.Column("overlay_image_path", sa.String(500), nullable=False),
        sa.Column("crop_name", sa.String(50), nullable=False),
        sa.Column(
            "disease_code",
            sa.String(100),
            sa.ForeignKey("diseases_reference.disease_code"),
            nullable=False,
        ),
        sa.Column("disease_display_name", sa.String(150), nullable=False),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("infected_area_pct", sa.Float, nullable=False),
        sa.Column("severity", sa.Enum(*SEVERITY_LEVELS, name="severity_level"), nullable=False),
        sa.Column("model_version", sa.String(50), nullable=True),
        sa.Column("segmentation_backend", sa.String(50), nullable=True),
        sa.Column("model_status", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_scans_crop_name", "scans", ["crop_name"])
    op.create_index("idx_scans_severity", "scans", ["severity"])
    op.create_index("idx_scans_created_at", "scans", ["created_at"])

    op.create_table(
        "reports",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("report_id", sa.String(30), nullable=False, unique=True),
        sa.Column("scan_id", sa.Integer, sa.ForeignKey("scans.id"), nullable=False),
        sa.Column("pdf_path", sa.String(500), nullable=False),
        sa.Column("generated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("reports")
    op.drop_index("idx_scans_created_at", table_name="scans")
    op.drop_index("idx_scans_severity", table_name="scans")
    op.drop_index("idx_scans_crop_name", table_name="scans")
    op.drop_table("scans")
    op.drop_table("diseases_reference")
    sa.Enum(name="severity_level").drop(op.get_bind(), checkfirst=True)
