"""dynamic results and area validation

Revision ID: 0004_results_validation
Revises: 0003_clinical_mvp
Create Date: 2026-07-16
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_results_validation"
down_revision = "0003_clinical_mvp"
branch_labels = None
depends_on = None


def timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    ]


def upgrade() -> None:
    op.create_table(
        "result",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("order_item_id", sa.String(length=36), sa.ForeignKey("order_item.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="IN_PROCESS"),
        sa.Column("saved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("saved_by", sa.String(length=36), sa.ForeignKey("user.id", ondelete="SET NULL"), nullable=True),
        sa.Column("preliminary_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("preliminary_by", sa.String(length=36), sa.ForeignKey("user.id", ondelete="SET NULL"), nullable=True),
        sa.Column("final_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("final_by", sa.String(length=36), sa.ForeignKey("user.id", ondelete="SET NULL"), nullable=True),
        sa.CheckConstraint(
            "status IN ('IN_PROCESS', 'RESULT_SAVED', 'PRELIMINARY_VALIDATED', 'FINAL_VALIDATED')",
            name="ck_result_status",
        ),
        *timestamps(),
    )
    op.create_index("ix_result_order_item_id", "result", ["order_item_id"], unique=True)
    op.create_index("ix_result_status", "result", ["status"])

    op.create_table(
        "result_value",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("result_id", sa.String(length=36), sa.ForeignKey("result.id", ondelete="RESTRICT"), nullable=False),
        sa.Column(
            "parameter_definition_id",
            sa.String(length=36),
            sa.ForeignKey("parameter_definition.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("parameter_snapshot", sa.JSON(), nullable=False),
        sa.Column("value_text", sa.Text(), nullable=True),
        sa.Column("value_code", sa.String(length=250), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("result_id", "parameter_definition_id", name="uq_result_value_parameter"),
        sa.UniqueConstraint("result_id", "display_order", name="uq_result_value_display_order"),
        *timestamps(),
    )
    op.create_index("ix_result_value_result_id", "result_value", ["result_id"])


def downgrade() -> None:
    op.drop_table("result_value")
    op.drop_table("result")
