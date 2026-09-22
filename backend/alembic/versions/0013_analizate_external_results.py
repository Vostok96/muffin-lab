"""add external result support for Analizate

Revision ID: 0013_analizate_external_results
Revises: 0012_culture_params_all_exams
Create Date: 2026-09-22
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0013_analizate_external_results"
down_revision = "0012_culture_params_all_exams"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("exam", sa.Column("external_provider", sa.String(length=80), nullable=True))
    op.create_table(
        "result_attachment",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("order_item_id", sa.String(length=36), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("stored_name", sa.String(length=80), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=True),
        sa.Column("size_bytes", sa.Integer(), server_default="0", nullable=False),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("uploaded_by", sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(["order_item_id"], ["order_item.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["user.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_result_attachment_order_item_id"), "result_attachment", ["order_item_id"], unique=False)
    op.create_index(op.f("ix_result_attachment_stored_name"), "result_attachment", ["stored_name"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_result_attachment_stored_name"), table_name="result_attachment")
    op.drop_index(op.f("ix_result_attachment_order_item_id"), table_name="result_attachment")
    op.drop_table("result_attachment")
    op.drop_column("exam", "external_provider")
