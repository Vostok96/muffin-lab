"""minimum catalogs

Revision ID: 0002_minimum_catalogs
Revises: 0001_security_foundation
Create Date: 2026-07-15
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_minimum_catalogs"
down_revision = "0001_security_foundation"
branch_labels = None
depends_on = None


def timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    ]


def create_simple_catalog(table_name: str) -> None:
    op.create_table(
        table_name,
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *timestamps(),
    )
    op.create_index(f"ix_{table_name}_code", table_name, ["code"], unique=True)


def upgrade() -> None:
    create_simple_catalog("origin")
    create_simple_catalog("service")
    create_simple_catalog("container")

    op.create_table(
        "clinician",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("family_name", sa.String(length=120), nullable=False),
        sa.Column("given_name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *timestamps(),
    )
    op.create_index("ix_clinician_code", "clinician", ["code"], unique=True)

    op.create_table(
        "specimen_type",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("container_id", sa.String(length=36), sa.ForeignKey("container.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *timestamps(),
    )
    op.create_index("ix_specimen_type_code", "specimen_type", ["code"], unique=True)

    op.create_table(
        "exam",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("external_code", sa.String(length=80), nullable=True),
        sa.Column("barcode_suffix", sa.String(length=30), nullable=True),
        sa.Column("laboratory_area_id", sa.String(length=36), sa.ForeignKey("laboratory_area.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("sends_to_analyzer", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("requires_colony_count", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *timestamps(),
    )
    op.create_index("ix_exam_code", "exam", ["code"], unique=True)
    op.create_index("ix_exam_external_code", "exam", ["external_code"], unique=True)

    op.create_table(
        "parameter_definition",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("section", sa.String(length=120), nullable=True),
        sa.Column("value_type", sa.String(length=20), nullable=False),
        sa.Column("options_schema", sa.JSON(), nullable=True),
        sa.Column("methodology", sa.String(length=250), nullable=True),
        sa.Column("unit", sa.String(length=80), nullable=True),
        sa.Column("reference_low", sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column("reference_high", sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column("reference_text", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.CheckConstraint("value_type IN ('TEXT', 'LONG_TEXT', 'SELECT', 'DATE', 'DATETIME')", name="ck_parameter_definition_value_type"),
        *timestamps(),
    )
    op.create_index("ix_parameter_definition_code", "parameter_definition", ["code"], unique=True)

    op.create_table(
        "exam_specimen_type",
        sa.Column("exam_id", sa.String(length=36), sa.ForeignKey("exam.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("specimen_type_id", sa.String(length=36), sa.ForeignKey("specimen_type.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("is_favorite", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_table(
        "exam_parameter",
        sa.Column("exam_id", sa.String(length=36), sa.ForeignKey("exam.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("parameter_definition_id", sa.String(length=36), sa.ForeignKey("parameter_definition.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("external_code", sa.String(length=80), nullable=True),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.UniqueConstraint("exam_id", "display_order", name="uq_exam_parameter_display_order"),
    )


def downgrade() -> None:
    op.drop_table("exam_parameter")
    op.drop_table("exam_specimen_type")
    op.drop_table("parameter_definition")
    op.drop_table("exam")
    op.drop_table("specimen_type")
    op.drop_table("clinician")
    op.drop_table("container")
    op.drop_table("service")
    op.drop_table("origin")
