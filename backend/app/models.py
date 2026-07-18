from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import Boolean, CheckConstraint, Column, Date, DateTime, ForeignKey, Integer, JSON, Numeric, String, Table, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def new_id() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


user_roles = Table(
    "user_role",
    Base.metadata,
    Column("user_id", String(36), ForeignKey("user.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", String(36), ForeignKey("role.id", ondelete="CASCADE"), primary_key=True),
)


class TimestampedEntity:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class User(TimestampedEntity, Base):
    __tablename__ = "user"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    given_name: Mapped[str] = mapped_column(String(120), nullable=False)
    family_name: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    roles: Mapped[list["Role"]] = relationship(secondary=user_roles, lazy="selectin")
    area_permissions: Mapped[list["UserAreaPermission"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Role(Base):
    __tablename__ = "role"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)


class AppSetting(TimestampedEntity, Base):
    __tablename__ = "app_setting"

    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON, nullable=False)
    updated_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("user.id", ondelete="SET NULL"))


class LaboratoryArea(TimestampedEntity, Base):
    __tablename__ = "laboratory_area"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    section: Mapped[str] = mapped_column(String(80), default="MICROBIOLOGY", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    permissions: Mapped[list["UserAreaPermission"]] = relationship(back_populates="laboratory_area")


class Origin(TimestampedEntity, Base):
    __tablename__ = "origin"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Service(TimestampedEntity, Base):
    __tablename__ = "service"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Clinician(TimestampedEntity, Base):
    __tablename__ = "clinician"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    family_name: Mapped[str] = mapped_column(String(120), nullable=False)
    given_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str | None] = mapped_column(String(254))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Container(TimestampedEntity, Base):
    __tablename__ = "container"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Destination(TimestampedEntity, Base):
    __tablename__ = "destination"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class SpecimenType(TimestampedEntity, Base):
    __tablename__ = "specimen_type"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    container_id: Mapped[str] = mapped_column(String(36), ForeignKey("container.id", ondelete="RESTRICT"), nullable=False)
    parent_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("specimen_type.id", ondelete="RESTRICT"), index=True
    )
    is_selectable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Exam(TimestampedEntity, Base):
    __tablename__ = "exam"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    external_code: Mapped[str | None] = mapped_column(String(80), unique=True, index=True)
    barcode_suffix: Mapped[str | None] = mapped_column(String(30))
    laboratory_area_id: Mapped[str] = mapped_column(String(36), ForeignKey("laboratory_area.id", ondelete="RESTRICT"), nullable=False)
    sends_to_analyzer: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_colony_count: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ParameterDefinition(TimestampedEntity, Base):
    __tablename__ = "parameter_definition"
    __table_args__ = (
        CheckConstraint(
            "value_type IN ('TEXT', 'LONG_TEXT', 'SELECT', 'DATE', 'DATETIME')",
            name="ck_parameter_definition_value_type",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    section: Mapped[str | None] = mapped_column(String(120))
    value_type: Mapped[str] = mapped_column(String(20), nullable=False)
    options_schema: Mapped[dict | list | None] = mapped_column(JSON)
    methodology: Mapped[str | None] = mapped_column(String(250))
    unit: Mapped[str | None] = mapped_column(String(80))
    reference_low: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    reference_high: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    reference_text: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ExamSpecimenType(Base):
    __tablename__ = "exam_specimen_type"

    exam_id: Mapped[str] = mapped_column(String(36), ForeignKey("exam.id", ondelete="CASCADE"), primary_key=True)
    specimen_type_id: Mapped[str] = mapped_column(String(36), ForeignKey("specimen_type.id", ondelete="CASCADE"), primary_key=True)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class ExamParameter(Base):
    __tablename__ = "exam_parameter"
    __table_args__ = (UniqueConstraint("exam_id", "display_order", name="uq_exam_parameter_display_order"),)

    exam_id: Mapped[str] = mapped_column(String(36), ForeignKey("exam.id", ondelete="CASCADE"), primary_key=True)
    parameter_definition_id: Mapped[str] = mapped_column(String(36), ForeignKey("parameter_definition.id", ondelete="CASCADE"), primary_key=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
    external_code: Mapped[str | None] = mapped_column(String(80))
    is_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Patient(TimestampedEntity, Base):
    __tablename__ = "patient"
    __table_args__ = (CheckConstraint("sex IN ('F', 'M', 'X')", name="ck_patient_sex"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    medical_record_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    document_number: Mapped[str | None] = mapped_column(String(30), unique=True, index=True)
    family_name: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    given_name: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    sex: Mapped[str] = mapped_column(String(1), nullable=False)
    orders: Mapped[list["LabOrder"]] = relationship(back_populates="patient")


class LabOrder(TimestampedEntity, Base):
    __tablename__ = "lab_order"
    __table_args__ = (CheckConstraint("status IN ('DRAFT', 'REGISTERED', 'CANCELLED', 'CLOSED')", name="ck_lab_order_status"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    order_number: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    ordered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patient.id", ondelete="RESTRICT"), index=True, nullable=False)
    origin_id: Mapped[str] = mapped_column(String(36), ForeignKey("origin.id", ondelete="RESTRICT"), nullable=False)
    service_id: Mapped[str] = mapped_column(String(36), ForeignKey("service.id", ondelete="RESTRICT"), nullable=False)
    clinician_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("clinician.id", ondelete="RESTRICT"))
    clinical_notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="REGISTERED", index=True, nullable=False)
    patient: Mapped[Patient] = relationship(back_populates="orders", lazy="selectin")
    items: Mapped[list["OrderItem"]] = relationship(back_populates="lab_order", lazy="selectin", order_by="OrderItem.item_number")


class OrderItem(TimestampedEntity, Base):
    __tablename__ = "order_item"
    __table_args__ = (
        UniqueConstraint("lab_order_id", "item_number", name="uq_order_item_number"),
        CheckConstraint(
            "status IN ('REGISTERED', 'COLLECTED', 'RECEIVED', 'IN_PROCESS', 'RESULT_SAVED', "
            "'PRELIMINARY_VALIDATED', 'FINAL_VALIDATED', 'REJECTED', 'CANCELLED')",
            name="ck_order_item_status",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    lab_order_id: Mapped[str] = mapped_column(String(36), ForeignKey("lab_order.id", ondelete="RESTRICT"), index=True, nullable=False)
    item_number: Mapped[int] = mapped_column(Integer, nullable=False)
    exam_id: Mapped[str] = mapped_column(String(36), ForeignKey("exam.id", ondelete="RESTRICT"), nullable=False)
    specimen_type_id: Mapped[str] = mapped_column(String(36), ForeignKey("specimen_type.id", ondelete="RESTRICT"), nullable=False)
    barcode: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    collection_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    destination_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("destination.id", ondelete="RESTRICT"))
    specimen_notes: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(250))
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="REGISTERED", index=True, nullable=False)
    lab_order: Mapped[LabOrder] = relationship(back_populates="items")
    events: Mapped[list["WorkflowEvent"]] = relationship(back_populates="order_item", lazy="selectin", order_by="WorkflowEvent.occurred_at")
    result: Mapped["Result | None"] = relationship(back_populates="order_item", lazy="selectin", uselist=False)


class Result(TimestampedEntity, Base):
    __tablename__ = "result"
    __table_args__ = (
        CheckConstraint(
            "status IN ('IN_PROCESS', 'RESULT_SAVED', 'PRELIMINARY_VALIDATED', 'FINAL_VALIDATED')",
            name="ck_result_status",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    order_item_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("order_item.id", ondelete="RESTRICT"), unique=True, index=True, nullable=False
    )
    status: Mapped[str] = mapped_column(String(30), default="IN_PROCESS", index=True, nullable=False)
    saved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    saved_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("user.id", ondelete="SET NULL"))
    preliminary_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    preliminary_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("user.id", ondelete="SET NULL"))
    final_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    final_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("user.id", ondelete="SET NULL"))
    order_item: Mapped[OrderItem] = relationship(back_populates="result")
    values: Mapped[list["ResultValue"]] = relationship(
        back_populates="result",
        lazy="selectin",
        order_by="ResultValue.display_order",
        cascade="all, delete-orphan",
    )


class ResultValue(TimestampedEntity, Base):
    __tablename__ = "result_value"
    __table_args__ = (
        UniqueConstraint("result_id", "parameter_definition_id", name="uq_result_value_parameter"),
        UniqueConstraint("result_id", "display_order", name="uq_result_value_display_order"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    result_id: Mapped[str] = mapped_column(String(36), ForeignKey("result.id", ondelete="RESTRICT"), index=True, nullable=False)
    parameter_definition_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("parameter_definition.id", ondelete="RESTRICT"), nullable=False
    )
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    parameter_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    value_text: Mapped[str | None] = mapped_column(Text)
    value_code: Mapped[str | None] = mapped_column(String(250))
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    result: Mapped[Result] = relationship(back_populates="values")


class Organism(TimestampedEntity, Base):
    __tablename__ = "organism"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ColonyCountOption(TimestampedEntity, Base):
    __tablename__ = "colony_count_option"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class DefinedComment(TimestampedEntity, Base):
    __tablename__ = "defined_comment"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    text: Mapped[str] = mapped_column(String(500), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Antibiotic(TimestampedEntity, Base):
    __tablename__ = "antibiotic"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class AstPanel(TimestampedEntity, Base):
    __tablename__ = "ast_panel"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=999, server_default="999", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class AstPanelAntibiotic(Base):
    __tablename__ = "ast_panel_antibiotic"

    ast_panel_id: Mapped[str] = mapped_column(String(36), ForeignKey("ast_panel.id", ondelete="CASCADE"), primary_key=True)
    antibiotic_id: Mapped[str] = mapped_column(String(36), ForeignKey("antibiotic.id", ondelete="CASCADE"), primary_key=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
    default_method: Mapped[str | None] = mapped_column(String(80))
    default_interpretation: Mapped[str] = mapped_column(String(10), default="S", server_default="S", nullable=False)


class Isolate(TimestampedEntity, Base):
    __tablename__ = "isolate"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    result_id: Mapped[str] = mapped_column(String(36), ForeignKey("result.id", ondelete="RESTRICT"), index=True, nullable=False)
    organism_id: Mapped[str] = mapped_column(String(36), ForeignKey("organism.id", ondelete="RESTRICT"), nullable=False)
    colony_count_option_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("colony_count_option.id", ondelete="RESTRICT"))
    phenotype: Mapped[str | None] = mapped_column(String(500))
    comment: Mapped[str | None] = mapped_column(Text)
    ast_panel_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("ast_panel.id", ondelete="RESTRICT"))


class AntimicrobialResult(TimestampedEntity, Base):
    __tablename__ = "antimicrobial_result"
    __table_args__ = (
        UniqueConstraint("isolate_id", "antibiotic_id", name="uq_antimicrobial_result_isolate_antibiotic"),
        CheckConstraint(
            "interpretation IN ('S', 'SDD', 'I', 'R', 'POS', 'NEG', 'NA')",
            name="ck_antimicrobial_result_interpretation",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    isolate_id: Mapped[str] = mapped_column(String(36), ForeignKey("isolate.id", ondelete="RESTRICT"), index=True, nullable=False)
    antibiotic_id: Mapped[str] = mapped_column(String(36), ForeignKey("antibiotic.id", ondelete="RESTRICT"), nullable=False)
    mic_value: Mapped[str | None] = mapped_column(String(80))
    interpretation: Mapped[str] = mapped_column(String(10), nullable=False)
    method: Mapped[str | None] = mapped_column(String(80))
    is_reportable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class WorkflowEvent(Base):
    __tablename__ = "workflow_event"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    order_item_id: Mapped[str] = mapped_column(String(36), ForeignKey("order_item.id", ondelete="RESTRICT"), index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True, nullable=False)
    performed_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("user.id", ondelete="SET NULL"))
    details: Mapped[dict | None] = mapped_column(JSON)
    order_item: Mapped[OrderItem] = relationship(back_populates="events")


class UserAreaPermission(TimestampedEntity, Base):
    __tablename__ = "user_area_permission"
    __table_args__ = (UniqueConstraint("user_id", "laboratory_area_id", name="uq_user_area_permission"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    laboratory_area_id: Mapped[str] = mapped_column(String(36), ForeignKey("laboratory_area.id", ondelete="CASCADE"), nullable=False)
    can_preliminary_validate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_final_validate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    user: Mapped[User] = relationship(back_populates="area_permissions")
    laboratory_area: Mapped[LaboratoryArea] = relationship(back_populates="permissions")


class AuditEvent(Base):
    __tablename__ = "audit_event"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    actor_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("user.id", ondelete="SET NULL"))
    entity_type: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(36), index=True)
    action: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True, nullable=False)
    before_data: Mapped[dict | None] = mapped_column(JSON)
    after_data: Mapped[dict | None] = mapped_column(JSON)
    reason: Mapped[str | None] = mapped_column(Text)


class PrintJob(TimestampedEntity, Base):
    __tablename__ = "print_job"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('LABEL', 'BARCODE', 'REPORT')",
            name="ck_print_job_kind",
        ),
        CheckConstraint(
            "status IN ('PENDING', 'PRINTED', 'FAILED')",
            name="ck_print_job_status",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    order_item_id: Mapped[str] = mapped_column(String(36), ForeignKey("order_item.id", ondelete="RESTRICT"), index=True, nullable=False)
    kind: Mapped[str] = mapped_column(String(30), nullable=False)
    requested_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("user.id", ondelete="SET NULL"))
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False)
    printed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    details: Mapped[str | None] = mapped_column(Text)


class Notification(TimestampedEntity, Base):
    __tablename__ = "notification"
    __table_args__ = (
        CheckConstraint(
            "type IN ('RESULT_READY', 'CRITICAL_VALUE', 'SPECIMEN_REJECTED', 'REPORT_AVAILABLE', 'CUSTOM')",
            name="ck_notification_type",
        ),
        CheckConstraint(
            "status IN ('PENDING', 'SENT', 'FAILED')",
            name="ck_notification_status",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    order_item_id: Mapped[str] = mapped_column(String(36), ForeignKey("order_item.id", ondelete="RESTRICT"), index=True, nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    recipient: Mapped[str] = mapped_column(String(254), nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)


class InstrumentMessage(TimestampedEntity, Base):
    __tablename__ = "instrument_message"
    __table_args__ = (
        CheckConstraint(
            "direction IN ('INBOUND', 'OUTBOUND')",
            name="ck_instrument_message_direction",
        ),
        CheckConstraint(
            "status IN ('PENDING', 'PROCESSED', 'FAILED', 'ACKNOWLEDGED')",
            name="ck_instrument_message_status",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    order_item_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("order_item.id", ondelete="RESTRICT"), index=True)
    direction: Mapped[str] = mapped_column(String(20), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    result_summary: Mapped[str | None] = mapped_column(Text)
