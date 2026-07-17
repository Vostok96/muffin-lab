"""outputs and integrations: print jobs, notifications, instrument messages

Revision ID: 0006_outputs_integrations
Revises: 0005_microbiology_advanced
Create Date: 2026-07-16
"""

from alembic import op
import sqlalchemy as sa


revision = "0006_outputs_integrations"
down_revision = "0005_microbiology_advanced"
branch_labels = None
depends_on = None


def timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    ]


def upgrade() -> None:
    op.create_table(
        "print_job",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("order_item_id", sa.String(length=36), sa.ForeignKey("order_item.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("kind", sa.String(length=30), nullable=False),
        sa.Column("requested_by", sa.String(length=36), sa.ForeignKey("user.id", ondelete="SET NULL"), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="PENDING"),
        sa.Column("printed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.CheckConstraint("kind IN ('LABEL', 'BARCODE', 'REPORT')", name="ck_print_job_kind"),
        sa.CheckConstraint("status IN ('PENDING', 'PRINTED', 'FAILED')", name="ck_print_job_status"),
        *timestamps(),
    )
    op.create_index("ix_print_job_order_item_id", "print_job", ["order_item_id"])

    op.create_table(
        "notification",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("order_item_id", sa.String(length=36), sa.ForeignKey("order_item.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("recipient", sa.String(length=254), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="PENDING"),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "type IN ('RESULT_READY', 'CRITICAL_VALUE', 'SPECIMEN_REJECTED', 'REPORT_AVAILABLE', 'CUSTOM')",
            name="ck_notification_type",
        ),
        sa.CheckConstraint("status IN ('PENDING', 'SENT', 'FAILED')", name="ck_notification_status"),
        *timestamps(),
    )
    op.create_index("ix_notification_order_item_id", "notification", ["order_item_id"])

    op.create_table(
        "instrument_message",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("order_item_id", sa.String(length=36), sa.ForeignKey("order_item.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("direction", sa.String(length=20), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="PENDING"),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("result_summary", sa.Text(), nullable=True),
        sa.CheckConstraint("direction IN ('INBOUND', 'OUTBOUND')", name="ck_instrument_message_direction"),
        sa.CheckConstraint(
            "status IN ('PENDING', 'PROCESSED', 'FAILED', 'ACKNOWLEDGED')",
            name="ck_instrument_message_status",
        ),
        *timestamps(),
    )
    op.create_index("ix_instrument_message_order_item_id", "instrument_message", ["order_item_id"])


def downgrade() -> None:
    op.drop_table("instrument_message")
    op.drop_table("notification")
    op.drop_table("print_job")
