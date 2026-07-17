"""clinical MVP and specimen traceability

Revision ID: 0003_clinical_mvp
Revises: 0002_minimum_catalogs
Create Date: 2026-07-16
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_clinical_mvp"
down_revision = "0002_minimum_catalogs"
branch_labels = None
depends_on = None


def timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    ]


def upgrade() -> None:
    op.execute(sa.schema.CreateSequence(sa.Sequence("lab_order_number_seq", start=1)))

    op.create_table(
        "destination",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *timestamps(),
    )
    op.create_index("ix_destination_code", "destination", ["code"], unique=True)

    op.create_table(
        "patient",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("medical_record_number", sa.String(length=50), nullable=False),
        sa.Column("document_number", sa.String(length=30), nullable=True),
        sa.Column("family_name", sa.String(length=120), nullable=False),
        sa.Column("given_name", sa.String(length=120), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=False),
        sa.Column("sex", sa.String(length=1), nullable=False),
        sa.CheckConstraint("sex IN ('F', 'M', 'X')", name="ck_patient_sex"),
        *timestamps(),
    )
    op.create_index("ix_patient_medical_record_number", "patient", ["medical_record_number"], unique=True)
    op.create_index("ix_patient_document_number", "patient", ["document_number"], unique=True)
    op.create_index("ix_patient_family_name", "patient", ["family_name"])
    op.create_index("ix_patient_given_name", "patient", ["given_name"])

    op.create_table(
        "lab_order",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("order_number", sa.String(length=40), nullable=False),
        sa.Column("ordered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("patient_id", sa.String(length=36), sa.ForeignKey("patient.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("origin_id", sa.String(length=36), sa.ForeignKey("origin.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("service_id", sa.String(length=36), sa.ForeignKey("service.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("clinician_id", sa.String(length=36), sa.ForeignKey("clinician.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("clinical_notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="REGISTERED"),
        sa.CheckConstraint("status IN ('DRAFT', 'REGISTERED', 'CANCELLED', 'CLOSED')", name="ck_lab_order_status"),
        *timestamps(),
    )
    op.create_index("ix_lab_order_order_number", "lab_order", ["order_number"], unique=True)
    op.create_index("ix_lab_order_ordered_at", "lab_order", ["ordered_at"])
    op.create_index("ix_lab_order_patient_id", "lab_order", ["patient_id"])
    op.create_index("ix_lab_order_status", "lab_order", ["status"])

    op.create_table(
        "order_item",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("lab_order_id", sa.String(length=36), sa.ForeignKey("lab_order.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("item_number", sa.Integer(), nullable=False),
        sa.Column("exam_id", sa.String(length=36), sa.ForeignKey("exam.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("specimen_type_id", sa.String(length=36), sa.ForeignKey("specimen_type.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("barcode", sa.String(length=100), nullable=False),
        sa.Column("collection_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("destination_id", sa.String(length=36), sa.ForeignKey("destination.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("specimen_notes", sa.Text(), nullable=True),
        sa.Column("location", sa.String(length=250), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="REGISTERED"),
        sa.CheckConstraint(
            "status IN ('REGISTERED', 'COLLECTED', 'RECEIVED', 'IN_PROCESS', 'RESULT_SAVED', "
            "'PRELIMINARY_VALIDATED', 'FINAL_VALIDATED', 'REJECTED', 'CANCELLED')",
            name="ck_order_item_status",
        ),
        sa.UniqueConstraint("lab_order_id", "item_number", name="uq_order_item_number"),
        *timestamps(),
    )
    op.create_index("ix_order_item_lab_order_id", "order_item", ["lab_order_id"])
    op.create_index("ix_order_item_barcode", "order_item", ["barcode"], unique=True)
    op.create_index("ix_order_item_status", "order_item", ["status"])

    op.create_table(
        "workflow_event",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("order_item_id", sa.String(length=36), sa.ForeignKey("order_item.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("performed_by", sa.String(length=36), sa.ForeignKey("user.id", ondelete="SET NULL"), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
    )
    op.create_index("ix_workflow_event_order_item_id", "workflow_event", ["order_item_id"])
    op.create_index("ix_workflow_event_event_type", "workflow_event", ["event_type"])
    op.create_index("ix_workflow_event_occurred_at", "workflow_event", ["occurred_at"])


def downgrade() -> None:
    op.drop_table("workflow_event")
    op.drop_table("order_item")
    op.drop_table("lab_order")
    op.drop_table("patient")
    op.drop_table("destination")
    op.execute(sa.schema.DropSequence(sa.Sequence("lab_order_number_seq")))
