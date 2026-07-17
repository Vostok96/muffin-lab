from datetime import date, datetime
from decimal import Decimal
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class InputModel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)


class LoginRequest(InputModel):
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=3, max_length=256)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class AreaPermissionInput(InputModel):
    laboratory_area_id: str
    can_preliminary_validate: bool = False
    can_final_validate: bool = False


class UserCreate(InputModel):
    username: str = Field(min_length=3, max_length=80, pattern=r"^[a-zA-Z0-9._-]+$")
    given_name: str = Field(min_length=1, max_length=120)
    family_name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=4, max_length=256)
    role_codes: list[str] = Field(min_length=1)
    area_permissions: list[AreaPermissionInput] = Field(default_factory=list)


class UserUpdate(InputModel):
    given_name: str | None = Field(default=None, min_length=1, max_length=120)
    family_name: str | None = Field(default=None, min_length=1, max_length=120)
    password: str | None = Field(default=None, min_length=4, max_length=256)
    role_codes: list[str] | None = None
    is_active: bool | None = None


class RoleUpdate(InputModel):
    role_codes: list[str] = Field(min_length=1)


class LaboratoryAreaCreate(InputModel):
    code: str = Field(min_length=2, max_length=50, pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=2, max_length=120)
    section: str = Field(default="MICROBIOLOGY", min_length=2, max_length=80)


class AreaPermissionUpdate(InputModel):
    area_permissions: list[AreaPermissionInput]


class UserResponse(BaseModel):
    id: str
    username: str
    given_name: str
    family_name: str
    is_active: bool
    roles: list[str]


class AuditEventResponse(BaseModel):
    id: str
    actor_user_id: str | None
    entity_type: str
    entity_id: str | None
    action: str
    occurred_at: datetime
    reason: str | None


class CatalogCreate(InputModel):
    code: str = Field(min_length=2, max_length=50, pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=2, max_length=120)
    is_active: bool = True


class CatalogUpdate(InputModel):
    code: str | None = Field(default=None, min_length=2, max_length=50, pattern=r"^[A-Za-z0-9_-]+$")
    name: str | None = Field(default=None, min_length=2, max_length=120)
    is_active: bool | None = None


class LaboratoryAreaUpdate(CatalogUpdate):
    section: str | None = Field(default=None, min_length=2, max_length=80)


class ClinicianCreate(InputModel):
    code: str = Field(min_length=2, max_length=50, pattern=r"^[A-Za-z0-9_-]+$")
    family_name: str = Field(min_length=1, max_length=120)
    given_name: str = Field(min_length=1, max_length=120)
    email: str | None = Field(default=None, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    is_active: bool = True


class ClinicianUpdate(InputModel):
    code: str | None = Field(default=None, min_length=2, max_length=50, pattern=r"^[A-Za-z0-9_-]+$")
    family_name: str | None = Field(default=None, min_length=1, max_length=120)
    given_name: str | None = Field(default=None, min_length=1, max_length=120)
    email: str | None = Field(default=None, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    is_active: bool | None = None


class SpecimenTypeCreate(CatalogCreate):
    container_id: str
    parent_id: str | None = None
    is_selectable: bool = True


class SpecimenTypeUpdate(CatalogUpdate):
    container_id: str | None = None
    parent_id: str | None = None
    is_selectable: bool | None = None


class ExamCreate(InputModel):
    code: str = Field(min_length=2, max_length=50, pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=2, max_length=180)
    external_code: str | None = Field(default=None, max_length=80)
    barcode_suffix: str | None = Field(default=None, max_length=30)
    laboratory_area_id: str
    sends_to_analyzer: bool = False
    requires_colony_count: bool = False
    is_active: bool = True


class ExamUpdate(InputModel):
    code: str | None = Field(default=None, min_length=2, max_length=50, pattern=r"^[A-Za-z0-9_-]+$")
    name: str | None = Field(default=None, min_length=2, max_length=180)
    external_code: str | None = Field(default=None, max_length=80)
    barcode_suffix: str | None = Field(default=None, max_length=30)
    laboratory_area_id: str | None = None
    sends_to_analyzer: bool | None = None
    requires_colony_count: bool | None = None
    is_active: bool | None = None


ParameterValueType = Literal["TEXT", "LONG_TEXT", "SELECT", "DATE", "DATETIME"]


class ParameterDefinitionCreate(InputModel):
    code: str = Field(min_length=2, max_length=50, pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=2, max_length=180)
    section: str | None = Field(default=None, max_length=120)
    value_type: ParameterValueType
    options_schema: list[Any] | dict | None = None
    methodology: str | None = Field(default=None, max_length=250)
    unit: str | None = Field(default=None, max_length=80)
    reference_low: Decimal | None = None
    reference_high: Decimal | None = None
    reference_text: str | None = None
    is_active: bool = True

    @model_validator(mode="after")
    def validate_definition(self) -> "ParameterDefinitionCreate":
        if self.value_type == "SELECT" and not self.options_schema:
            raise ValueError("options_schema is required for SELECT parameters.")
        if self.value_type != "SELECT" and self.options_schema is not None:
            raise ValueError("options_schema is only valid for SELECT parameters.")
        if self.reference_low is not None and self.reference_high is not None and self.reference_low > self.reference_high:
            raise ValueError("reference_low cannot be greater than reference_high.")
        return self


class ParameterDefinitionUpdate(InputModel):
    code: str | None = Field(default=None, min_length=2, max_length=50, pattern=r"^[A-Za-z0-9_-]+$")
    name: str | None = Field(default=None, min_length=2, max_length=180)
    section: str | None = Field(default=None, max_length=120)
    value_type: ParameterValueType | None = None
    options_schema: list[Any] | dict | None = None
    methodology: str | None = Field(default=None, max_length=250)
    unit: str | None = Field(default=None, max_length=80)
    reference_low: Decimal | None = None
    reference_high: Decimal | None = None
    reference_text: str | None = None
    is_active: bool | None = None


class ExamSpecimenTypeInput(InputModel):
    is_favorite: bool = False


class ExamParameterInput(InputModel):
    display_order: int = Field(ge=1)
    external_code: str | None = Field(default=None, max_length=80)
    is_required: bool = False


class TimestampedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime


class CatalogResponse(TimestampedResponse):
    code: str
    name: str
    is_active: bool


class LaboratoryAreaResponse(CatalogResponse):
    section: str


class ClinicianResponse(TimestampedResponse):
    code: str
    family_name: str
    given_name: str
    email: str | None
    is_active: bool


class SpecimenTypeResponse(CatalogResponse):
    container_id: str
    parent_id: str | None
    is_selectable: bool


class ExamResponse(TimestampedResponse):
    code: str
    name: str
    external_code: str | None
    barcode_suffix: str | None
    laboratory_area_id: str
    sends_to_analyzer: bool
    requires_colony_count: bool
    is_active: bool


class ParameterDefinitionResponse(TimestampedResponse):
    code: str
    name: str
    section: str | None
    value_type: ParameterValueType
    options_schema: list[Any] | dict | None
    methodology: str | None
    unit: str | None
    reference_low: Decimal | None
    reference_high: Decimal | None
    reference_text: str | None
    is_active: bool


class ExamSpecimenTypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    exam_id: str
    specimen_type_id: str
    is_favorite: bool


class ExamParameterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    exam_id: str
    parameter_definition_id: str
    display_order: int
    external_code: str | None
    is_required: bool


ResponseT = TypeVar("ResponseT")


class CatalogPage(BaseModel, Generic[ResponseT]):
    data: list[ResponseT]
    page: int
    page_size: int
    total: int


Sex = Literal["F", "M", "X"]
OrderStatus = Literal["DRAFT", "REGISTERED", "CANCELLED", "CLOSED"]
OrderItemStatus = Literal[
    "REGISTERED",
    "COLLECTED",
    "RECEIVED",
    "IN_PROCESS",
    "RESULT_SAVED",
    "PRELIMINARY_VALIDATED",
    "FINAL_VALIDATED",
    "REJECTED",
    "CANCELLED",
]


def ensure_timezone(value: datetime | None) -> datetime | None:
    if value is not None and (value.tzinfo is None or value.utcoffset() is None):
        raise ValueError("Datetime values must include a timezone offset.")
    return value


class PatientCreate(InputModel):
    medical_record_number: str = Field(min_length=1, max_length=50, pattern=r"^[A-Za-z0-9._/-]+$")
    document_number: str | None = Field(default=None, min_length=1, max_length=30, pattern=r"^[A-Za-z0-9._-]+$")
    family_name: str = Field(min_length=1, max_length=120)
    given_name: str = Field(min_length=1, max_length=120)
    birth_date: date
    sex: Sex

    @field_validator("birth_date")
    @classmethod
    def birth_date_cannot_be_future(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("birth_date cannot be in the future.")
        return value


class PatientUpdate(InputModel):
    medical_record_number: str | None = Field(default=None, min_length=1, max_length=50, pattern=r"^[A-Za-z0-9._/-]+$")
    document_number: str | None = Field(default=None, min_length=1, max_length=30, pattern=r"^[A-Za-z0-9._-]+$")
    family_name: str | None = Field(default=None, min_length=1, max_length=120)
    given_name: str | None = Field(default=None, min_length=1, max_length=120)
    birth_date: date | None = None
    sex: Sex | None = None

    @field_validator("birth_date")
    @classmethod
    def birth_date_cannot_be_future(cls, value: date | None) -> date | None:
        if value is not None and value > date.today():
            raise ValueError("birth_date cannot be in the future.")
        return value


class PatientResponse(TimestampedResponse):
    medical_record_number: str
    document_number: str | None
    family_name: str
    given_name: str
    birth_date: date
    sex: Sex


class PatientPage(BaseModel):
    data: list[PatientResponse]
    page: int
    page_size: int
    total: int


class OrderCreate(InputModel):
    patient_id: str
    ordered_at: datetime
    origin_id: str
    service_id: str
    clinician_id: str | None = None
    clinical_notes: str | None = Field(default=None, max_length=4000)

    _ordered_at_timezone = field_validator("ordered_at")(ensure_timezone)


class OrderUpdate(InputModel):
    ordered_at: datetime | None = None
    origin_id: str | None = None
    service_id: str | None = None
    clinician_id: str | None = None
    clinical_notes: str | None = Field(default=None, max_length=4000)

    _ordered_at_timezone = field_validator("ordered_at")(ensure_timezone)


class OrderItemCreate(InputModel):
    exam_id: str
    specimen_type_id: str
    collection_at: datetime | None = None
    specimen_notes: str | None = Field(default=None, max_length=2000)
    location: str | None = Field(default=None, max_length=250)

    _collection_at_timezone = field_validator("collection_at")(ensure_timezone)


class CollectSpecimenInput(InputModel):
    collection_at: datetime
    specimen_notes: str | None = Field(default=None, max_length=2000)
    location: str | None = Field(default=None, max_length=250)

    _collection_at_timezone = field_validator("collection_at")(ensure_timezone)


class ReceiveSpecimenInput(InputModel):
    received_at: datetime
    destination_id: str
    collection_at: datetime | None = None
    specimen_notes: str | None = Field(default=None, max_length=2000)
    location: str | None = Field(default=None, max_length=250)

    _received_at_timezone = field_validator("received_at")(ensure_timezone)
    _collection_at_timezone = field_validator("collection_at")(ensure_timezone)


class SpecimenDetailsUpdate(InputModel):
    collection_at: datetime | None = None
    received_at: datetime | None = None
    specimen_notes: str | None = Field(default=None, max_length=2000)
    location: str | None = Field(default=None, max_length=250)

    _collection_at_timezone = field_validator("collection_at")(ensure_timezone)
    _received_at_timezone = field_validator("received_at")(ensure_timezone)


class ReasonInput(InputModel):
    reason: str = Field(min_length=5, max_length=2000)


class WorkflowEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    order_item_id: str
    event_type: str
    occurred_at: datetime
    performed_by: str | None
    details: dict | None


class OrderItemResponse(TimestampedResponse):
    lab_order_id: str
    item_number: int
    exam_id: str
    specimen_type_id: str
    barcode: str
    collection_at: datetime | None
    received_at: datetime | None
    destination_id: str | None
    specimen_notes: str | None
    location: str | None
    rejection_reason: str | None
    status: OrderItemStatus
    events: list[WorkflowEventResponse] = Field(default_factory=list)


class OrderResponse(TimestampedResponse):
    order_number: str
    ordered_at: datetime
    patient_id: str
    origin_id: str
    service_id: str
    clinician_id: str | None
    clinical_notes: str | None
    status: OrderStatus
    items: list[OrderItemResponse] = Field(default_factory=list)


class OrderPage(BaseModel):
    data: list[OrderResponse]
    page: int
    page_size: int
    total: int


ResultStatus = Literal["IN_PROCESS", "RESULT_SAVED", "PRELIMINARY_VALIDATED", "FINAL_VALIDATED"]
ResultResponseStatus = Literal["NOT_STARTED", "IN_PROCESS", "RESULT_SAVED", "PRELIMINARY_VALIDATED", "FINAL_VALIDATED"]


class ResultValueInput(InputModel):
    parameter_definition_id: str
    value_text: str | None = Field(default=None, max_length=10000)
    value_code: str | None = Field(default=None, max_length=250)
    observed_at: datetime | None = None

    _observed_at_timezone = field_validator("observed_at")(ensure_timezone)


class ResultSaveInput(InputModel):
    values: list[ResultValueInput] = Field(max_length=500)
    ready_for_validation: bool = False

    @model_validator(mode="after")
    def values_must_be_unique(self) -> "ResultSaveInput":
        parameter_ids = [value.parameter_definition_id for value in self.values]
        if len(parameter_ids) != len(set(parameter_ids)):
            raise ValueError("Each parameter_definition_id can only appear once.")
        return self


class ResultParameterResponse(BaseModel):
    parameter_definition_id: str
    code: str
    name: str
    section: str | None
    value_type: ParameterValueType
    options_schema: list[Any] | dict | None
    methodology: str | None
    unit: str | None
    reference_low: Decimal | None
    reference_high: Decimal | None
    reference_text: str | None
    display_order: int
    is_required: bool
    value_text: str | None
    value_code: str | None
    observed_at: datetime | None


class ResultResponse(BaseModel):
    id: str | None
    order_item_id: str
    status: ResultResponseStatus
    saved_at: datetime | None
    saved_by: str | None
    preliminary_at: datetime | None
    preliminary_by: str | None
    final_at: datetime | None
    final_by: str | None
    values: list[ResultParameterResponse]


# ---------------------------------------------------------------------------
# Microbiology advanced — Phase 5
# ---------------------------------------------------------------------------


class OrganismCreate(CatalogCreate):
    pass


class OrganismUpdate(CatalogUpdate):
    pass


class OrganismResponse(CatalogResponse):
    pass


class ColonyCountOptionCreate(CatalogCreate):
    pass


class ColonyCountOptionUpdate(CatalogUpdate):
    pass


class ColonyCountOptionResponse(CatalogResponse):
    pass


class DefinedCommentCreate(InputModel):
    code: str = Field(min_length=2, max_length=50, pattern=r"^[A-Za-z0-9_-]+$")
    text: str = Field(min_length=2, max_length=500)
    is_active: bool = True


class DefinedCommentUpdate(InputModel):
    code: str | None = Field(default=None, min_length=2, max_length=50, pattern=r"^[A-Za-z0-9_-]+$")
    text: str | None = Field(default=None, min_length=2, max_length=500)
    is_active: bool | None = None


class DefinedCommentResponse(TimestampedResponse):
    code: str
    text: str
    is_active: bool


class AntibioticCreate(CatalogCreate):
    pass


class AntibioticUpdate(CatalogUpdate):
    pass


class AntibioticResponse(CatalogResponse):
    pass


class AstPanelCreate(CatalogCreate):
    display_order: int = Field(default=999, ge=1)


class AstPanelUpdate(CatalogUpdate):
    display_order: int | None = Field(default=None, ge=1)


class AstPanelResponse(CatalogResponse):
    display_order: int


AntimicrobialInterpretation = Literal["S", "SDD", "I", "R", "POS", "NEG", "NA"]


class AstPanelAntibioticInput(InputModel):
    display_order: int = Field(ge=1)
    default_method: str | None = Field(default=None, max_length=80)
    default_interpretation: AntimicrobialInterpretation = "S"


class AstPanelAntibioticResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ast_panel_id: str
    antibiotic_id: str
    display_order: int
    default_method: str | None
    default_interpretation: str


IsolateStatus = Literal["IN_PROCESS", "IDENTIFIED", "AST_PENDING", "AST_COMPLETE"]


class IsolateCreate(InputModel):
    organism_id: str
    colony_count_option_id: str | None = None
    phenotype: str | None = Field(default=None, max_length=500)
    comment: str | None = Field(default=None, max_length=4000)
    ast_panel_id: str | None = None


class IsolateUpdate(InputModel):
    organism_id: str | None = None
    colony_count_option_id: str | None = None
    phenotype: str | None = Field(default=None, max_length=500)
    comment: str | None = Field(default=None, max_length=4000)
    ast_panel_id: str | None = None


class AntimicrobialResultInput(InputModel):
    antibiotic_id: str
    mic_value: str | None = Field(default=None, max_length=80)
    interpretation: AntimicrobialInterpretation
    method: str | None = Field(default=None, max_length=80)
    is_reportable: bool = True


class AntimicrobialResultUpdate(InputModel):
    mic_value: str | None = Field(default=None, max_length=80)
    interpretation: AntimicrobialInterpretation | None = None
    method: str | None = Field(default=None, max_length=80)
    is_reportable: bool | None = None


class AntimicrobialResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    isolate_id: str
    antibiotic_id: str
    mic_value: str | None
    interpretation: str
    method: str | None
    is_reportable: bool
    created_at: datetime
    updated_at: datetime


class IsolateResponse(TimestampedResponse):
    result_id: str
    organism_id: str
    colony_count_option_id: str | None
    phenotype: str | None
    comment: str | None
    ast_panel_id: str | None


# ---------------------------------------------------------------------------
# Outputs and integrations — Phase 6
# ---------------------------------------------------------------------------

PrintJobKind = Literal["LABEL", "BARCODE", "REPORT"]
PrintJobStatus = Literal["PENDING", "PRINTED", "FAILED"]
NotificationType = Literal["RESULT_READY", "CRITICAL_VALUE", "SPECIMEN_REJECTED", "REPORT_AVAILABLE", "CUSTOM"]
NotificationStatus = Literal["PENDING", "SENT", "FAILED"]
InstrumentDirection = Literal["INBOUND", "OUTBOUND"]
InstrumentMessageStatus = Literal["PENDING", "PROCESSED", "FAILED", "ACKNOWLEDGED"]


class PrintJobCreate(InputModel):
    order_item_id: str
    kind: PrintJobKind
    details: str | None = Field(default=None, max_length=500)


class PrintJobResponse(TimestampedResponse):
    order_item_id: str
    kind: str
    requested_by: str | None
    requested_at: datetime
    status: str
    printed_at: datetime | None
    details: str | None


class NotificationCreate(InputModel):
    order_item_id: str
    type: NotificationType
    recipient: str = Field(max_length=254)
    payload: dict | None = None


class NotificationPatch(InputModel):
    status: NotificationStatus | None = None
    error_message: str | None = Field(default=None, max_length=2000)


class NotificationResponse(TimestampedResponse):
    order_item_id: str
    type: str
    recipient: str
    payload: dict | None
    status: str
    sent_at: datetime | None
    error_message: str | None


class InstrumentMessageCreate(InputModel):
    order_item_id: str | None = None
    direction: InstrumentDirection
    payload: dict
    result_summary: str | None = Field(default=None, max_length=2000)


class InstrumentMessagePatch(InputModel):
    status: InstrumentMessageStatus | None = None
    result_summary: str | None = Field(default=None, max_length=2000)


class InstrumentMessageResponse(TimestampedResponse):
    order_item_id: str | None
    direction: str
    payload: dict
    status: str
    processed_at: datetime | None
    result_summary: str | None
