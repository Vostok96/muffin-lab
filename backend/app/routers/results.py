from datetime import date, datetime, time, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.dependencies import get_current_user, require_area_validation, require_role
from app.models import (
    AntimicrobialResult,
    AstPanelAntibiotic,
    Clinician,
    Exam,
    ExamParameter,
    Isolate,
    LabOrder,
    OrderItem,
    Origin,
    ParameterDefinition,
    Patient,
    Result,
    ResultValue,
    Service,
    SpecimenType,
    User,
)
from app.schemas import ReasonInput, ResultParameterResponse, ResultResponse, ResultSaveInput, ResultValueInput
from app.services import derive_care_setting, parameter_definition_snapshot, record_audit, record_workflow_event


router = APIRouter(tags=["Results"])
result_writer = require_role("ADMIN", "PROCESS_ADMIN", "PROCESSOR")


@router.get("/result-worklist")
def list_result_worklist(
    date_from: date | None = Query(default=None, alias="from"),
    date_to: date | None = Query(default=None, alias="to"),
    search: str | None = Query(default=None, max_length=100),
    item_id: str | None = Query(default=None),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    filters = [OrderItem.status.notin_(("REJECTED", "CANCELLED"))]
    if date_from:
        filters.append(LabOrder.ordered_at >= datetime.combine(date_from, time.min, tzinfo=timezone.utc))
    if date_to:
        filters.append(LabOrder.ordered_at < datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=timezone.utc))
    if item_id:
        filters.append(OrderItem.id == item_id)
    if search:
        term = f"%{search.strip()}%"
        filters.append(
            or_(
                OrderItem.barcode.ilike(term),
                LabOrder.order_number.ilike(term),
                Patient.medical_record_number.ilike(term),
                Patient.family_name.ilike(term),
                Patient.given_name.ilike(term),
                Exam.name.ilike(term),
                SpecimenType.name.ilike(term),
            )
        )
    rows = db.execute(
        select(OrderItem, LabOrder, Patient, Exam, SpecimenType, Origin, Service, Clinician, Result)
        .join(LabOrder, LabOrder.id == OrderItem.lab_order_id)
        .join(Patient, Patient.id == LabOrder.patient_id)
        .join(Exam, Exam.id == OrderItem.exam_id)
        .join(SpecimenType, SpecimenType.id == OrderItem.specimen_type_id)
        .join(Origin, Origin.id == LabOrder.origin_id)
        .join(Service, Service.id == LabOrder.service_id)
        .outerjoin(Clinician, Clinician.id == LabOrder.clinician_id)
        .outerjoin(Result, Result.order_item_id == OrderItem.id)
        .where(*filters)
        .order_by(LabOrder.ordered_at.desc(), LabOrder.order_number.desc(), OrderItem.item_number)
    ).all()
    return [
        {
            "item": {
                "id": item.id,
                "barcode": item.barcode,
                "status": item.status,
                "collection_at": item.collection_at,
                "received_at": item.received_at,
                "specimen_notes": item.specimen_notes,
                "location": item.location,
            },
            "order": {
                "id": order.id,
                "order_number": order.order_number,
                "ordered_at": order.ordered_at,
                "clinical_notes": order.clinical_notes,
                "status": order.status,
                "care_setting": derive_care_setting(origin.code, origin.name, service.code, service.name),
            },
            "patient": {
                "id": patient.id,
                "medical_record_number": patient.medical_record_number,
                "family_name": patient.family_name,
                "given_name": patient.given_name,
                "birth_date": patient.birth_date,
                "sex": patient.sex,
            },
            "exam": {
                "id": exam.id,
                "code": exam.code,
                "name": exam.name,
                "laboratory_area_id": exam.laboratory_area_id,
                "sends_to_analyzer": exam.sends_to_analyzer,
                "requires_colony_count": exam.requires_colony_count,
            },
            "specimen": {"id": specimen.id, "code": specimen.code, "name": specimen.name},
            "origin": {"id": origin.id, "code": origin.code, "name": origin.name},
            "service": {"id": service.id, "code": service.code, "name": service.name},
            "clinician": (
                {
                    "id": clinician.id,
                    "code": clinician.code,
                    "family_name": clinician.family_name,
                    "given_name": clinician.given_name,
                }
                if clinician
                else None
            ),
            "result": (
                {
                    "id": result.id,
                    "status": result.status,
                    "saved_at": result.saved_at,
                    "preliminary_at": result.preliminary_at,
                    "final_at": result.final_at,
                }
                if result
                else None
            ),
        }
        for item, order, patient, exam, specimen, origin, service, clinician, result in rows
    ]


def validation_error(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=detail)


def get_order_item(db: Session, order_item_id: str, *, for_update: bool = False) -> OrderItem:
    statement = (
        select(OrderItem)
        .where(OrderItem.id == order_item_id)
        .options(selectinload(OrderItem.result).selectinload(Result.values))
    )
    if for_update:
        statement = statement.with_for_update()
    item = db.scalar(statement)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order item not found.")
    return item


def get_result(db: Session, order_item_id: str) -> Result | None:
    return db.scalar(
        select(Result)
        .where(Result.order_item_id == order_item_id)
        .options(selectinload(Result.values))
    )


def get_exam_parameters(db: Session, exam_id: str) -> list[tuple[ExamParameter, ParameterDefinition]]:
    return list(
        db.execute(
            select(ExamParameter, ParameterDefinition)
            .join(
                ParameterDefinition,
                ParameterDefinition.id == ExamParameter.parameter_definition_id,
            )
            .where(ExamParameter.exam_id == exam_id)
            .order_by(ExamParameter.display_order, ParameterDefinition.code)
        ).tuples()
    )


def parameter_response(
    *,
    parameter_definition_id: str,
    display_order: int,
    is_required: bool,
    snapshot: dict[str, Any],
    value_text: str | None = None,
    value_code: str | None = None,
    observed_at: datetime | None = None,
) -> ResultParameterResponse:
    return ResultParameterResponse(
        parameter_definition_id=parameter_definition_id,
        code=snapshot["code"],
        name=snapshot["name"],
        section=snapshot.get("section"),
        value_type=snapshot["value_type"],
        options_schema=snapshot.get("options_schema"),
        methodology=snapshot.get("methodology"),
        unit=snapshot.get("unit"),
        reference_low=snapshot.get("reference_low"),
        reference_high=snapshot.get("reference_high"),
        reference_text=snapshot.get("reference_text"),
        display_order=display_order,
        is_required=is_required,
        value_text=value_text,
        value_code=value_code,
        observed_at=observed_at,
    )


def result_response(db: Session, item: OrderItem) -> ResultResponse:
    result = get_result(db, item.id)
    if result:
        values = [
            parameter_response(
                parameter_definition_id=value.parameter_definition_id,
                display_order=value.display_order,
                is_required=value.is_required,
                snapshot=value.parameter_snapshot,
                value_text=value.value_text,
                value_code=value.value_code,
                observed_at=value.observed_at,
            )
            for value in result.values
        ]
        return ResultResponse(
            id=result.id,
            order_item_id=item.id,
            status=result.status,
            saved_at=result.saved_at,
            saved_by=result.saved_by,
            preliminary_at=result.preliminary_at,
            preliminary_by=result.preliminary_by,
            final_at=result.final_at,
            final_by=result.final_by,
            values=values,
        )

    values = [
        parameter_response(
            parameter_definition_id=parameter.id,
            display_order=relation.display_order,
            is_required=relation.is_required,
            snapshot=parameter_definition_snapshot(parameter),
        )
        for relation, parameter in get_exam_parameters(db, item.exam_id)
    ]
    return ResultResponse(
        id=None,
        order_item_id=item.id,
        status="NOT_STARTED",
        saved_at=None,
        saved_by=None,
        preliminary_at=None,
        preliminary_by=None,
        final_at=None,
        final_by=None,
        values=values,
    )


def materialize_result(db: Session, item: OrderItem) -> Result:
    configured = get_exam_parameters(db, item.exam_id)
    if not configured:
        raise validation_error("The exam has no result parameters configured.")
    result = Result(order_item_id=item.id, status="IN_PROCESS")
    db.add(result)
    db.flush()
    result.values.extend(
        ResultValue(
            parameter_definition_id=parameter.id,
            display_order=relation.display_order,
            is_required=relation.is_required,
            parameter_snapshot=parameter_definition_snapshot(parameter),
        )
        for relation, parameter in configured
    )
    db.flush()
    return result


def select_options(options_schema: list | dict | None) -> dict[str, str]:
    if isinstance(options_schema, list):
        options: dict[str, str] = {}
        for option in options_schema:
            if isinstance(option, dict):
                code = option.get("code", option.get("value", option.get("id")))
                if code is None:
                    continue
                options[str(code)] = str(option.get("label", option.get("name", code)))
            else:
                text = str(option)
                options[text] = text
        return options
    if not isinstance(options_schema, dict):
        return {}
    raw_options = options_schema.get("options")
    if isinstance(raw_options, list):
        options: dict[str, str] = {}
        for option in raw_options:
            if isinstance(option, dict):
                code = option.get("code", option.get("value", option.get("id")))
                if code is not None:
                    options[str(code)] = str(option.get("label", option.get("name", code)))
            else:
                options[str(option)] = str(option)
        return options
    return {
        str(code): str(value.get("label", value.get("name", code)) if isinstance(value, dict) else value)
        for code, value in options_schema.items()
    }


def parse_datetime_value(value: str, parameter_code: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise validation_error(f"{parameter_code} must contain an ISO 8601 datetime.") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise validation_error(f"{parameter_code} must include a timezone offset.")
    return parsed.isoformat()


def normalize_value(
    row: ResultValue,
    submitted: ResultValueInput,
    current_parameter: ParameterDefinition | None = None,
) -> tuple[str | None, str | None, datetime | None]:
    value_text = submitted.value_text.strip() if submitted.value_text else None
    value_code = submitted.value_code.strip() if submitted.value_code else None
    value_type = row.parameter_snapshot["value_type"]
    parameter_code = row.parameter_snapshot["code"]

    if value_type == "SELECT":
        if value_text is None and value_code is None:
            return None, None, submitted.observed_at
        selected_code = value_code or value_text
        options = select_options(row.parameter_snapshot.get("options_schema"))
        if selected_code not in options and current_parameter is not None:
            current_options = select_options(parameter_definition_snapshot(current_parameter).get("options_schema"))
            if selected_code in current_options:
                return value_text or current_options[selected_code], selected_code, submitted.observed_at
        if selected_code not in options:
            raise validation_error(f"{parameter_code} contains an option that is not configured.")
        return value_text or options[selected_code], selected_code, submitted.observed_at

    if value_code is not None:
        raise validation_error(f"value_code is only valid for SELECT parameters ({parameter_code}).")
    if value_text is None:
        return None, None, submitted.observed_at
    if value_type == "DATE":
        try:
            value_text = date.fromisoformat(value_text).isoformat()
        except ValueError as error:
            raise validation_error(f"{parameter_code} must contain an ISO 8601 date.") from error
    elif value_type == "DATETIME":
        value_text = parse_datetime_value(value_text, parameter_code)
    return value_text, None, submitted.observed_at


OPTIONAL_RESULT_PARAMETER_CODES = {"CULTURE_NITRITE"}


def missing_required_values(result: Result) -> list[str]:
    return [
        value.parameter_snapshot["code"]
        for value in result.values
        if value.parameter_snapshot["code"] not in OPTIONAL_RESULT_PARAMETER_CODES
        and value.is_required
        and value.value_text is None
        and value.value_code is None
    ]


def restore_item_status_after_result_delete(item: OrderItem) -> str:
    if item.received_at:
        return "RECEIVED"
    if item.collection_at:
        return "COLLECTED"
    return "REGISTERED"


def delete_result_graph(db: Session, result: Result) -> None:
    isolates = list(db.scalars(select(Isolate).where(Isolate.result_id == result.id)))
    for isolate in isolates:
        for row in db.scalars(select(AntimicrobialResult).where(AntimicrobialResult.isolate_id == isolate.id)):
            db.delete(row)
        db.delete(isolate)
    for value in list(result.values):
        db.delete(value)
    db.delete(result)


def incomplete_ast_isolates(db: Session, result: Result) -> list[str]:
    incomplete = []
    isolates = list(db.scalars(select(Isolate).where(Isolate.result_id == result.id, Isolate.ast_panel_id.is_not(None))))
    for isolate in isolates:
        expected_panel_antibiotic = db.scalar(
            select(AstPanelAntibiotic).where(AstPanelAntibiotic.ast_panel_id == isolate.ast_panel_id).limit(1)
        )
        ast_rows = list(
            db.scalars(select(AntimicrobialResult).where(AntimicrobialResult.isolate_id == isolate.id))
        )
        if not ast_rows and expected_panel_antibiotic is None:
            continue
        if not ast_rows or any(row.interpretation == "NA" for row in ast_rows):
            incomplete.append(isolate.id)
    return incomplete


def result_snapshot(result: Result) -> dict[str, Any]:
    def iso(value: datetime | None) -> str | None:
        return value.isoformat() if value else None

    return {
        "status": result.status,
        "saved_at": iso(result.saved_at),
        "saved_by": result.saved_by,
        "preliminary_at": iso(result.preliminary_at),
        "preliminary_by": result.preliminary_by,
        "final_at": iso(result.final_at),
        "final_by": result.final_by,
        "values": [
            {
                "parameter_definition_id": value.parameter_definition_id,
                "value_text": value.value_text,
                "value_code": value.value_code,
                "observed_at": iso(value.observed_at),
            }
            for value in result.values
        ],
    }


def refresh_result_parameter_snapshots(db: Session, result: Result) -> None:
    parameter_ids = {value.parameter_definition_id for value in result.values}
    if not parameter_ids:
        return
    current_definitions = {
        parameter.id: parameter
        for parameter in db.scalars(select(ParameterDefinition).where(ParameterDefinition.id.in_(parameter_ids))).all()
    }
    for value in result.values:
        parameter = current_definitions.get(value.parameter_definition_id)
        if not parameter:
            continue
        current_snapshot = parameter_definition_snapshot(parameter)
        if value.parameter_snapshot != current_snapshot:
            value.parameter_snapshot = current_snapshot
            flag_modified(value, "parameter_snapshot")


def require_result(db: Session, item: OrderItem) -> Result:
    result = get_result(db, item.id)
    if not result:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="The result has not been saved yet.")
    return result


def require_exam_area(db: Session, item: OrderItem, *, final: bool, actor: User) -> Exam:
    exam = db.get(Exam, item.exam_id)
    if not exam:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="The order item exam no longer exists.")
    require_area_validation(exam.laboratory_area_id, final=final, user=actor)
    return exam


@router.get("/order-items/{order_item_id}/result", response_model=ResultResponse)
def get_order_item_result(
    order_item_id: str,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResultResponse:
    result = get_result(db, order_item_id)
    if result:
        refresh_result_parameter_snapshots(db, result)
    return result_response(db, get_order_item(db, order_item_id))


@router.put("/order-items/{order_item_id}/result", response_model=ResultResponse)
def save_order_item_result(
    order_item_id: str,
    payload: ResultSaveInput,
    actor: User = Depends(result_writer),
    db: Session = Depends(get_db),
) -> ResultResponse:
    item = get_order_item(db, order_item_id, for_update=True)
    if item.status not in {"RECEIVED", "IN_PROCESS", "RESULT_SAVED", "PRELIMINARY_VALIDATED", "FINAL_VALIDATED"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Results require a received specimen.")
    result = get_result(db, item.id)
    if result and result.status == "FINAL_VALIDATED":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Final validated results must be reopened before editing.")
    if not result:
        result = materialize_result(db, item)
    else:
        refresh_result_parameter_snapshots(db, result)

    before = result_snapshot(result)
    values_by_parameter = {value.parameter_definition_id: value for value in result.values}
    current_parameters = {parameter.id: parameter for _, parameter in get_exam_parameters(db, item.exam_id)}
    submitted_by_parameter = {value.parameter_definition_id: value for value in payload.values}
    unknown = sorted(set(submitted_by_parameter) - set(values_by_parameter))
    if unknown:
        raise validation_error(f"Parameters are not configured for this exam: {', '.join(unknown)}")

    for parameter_id, row in values_by_parameter.items():
        submitted = submitted_by_parameter.get(parameter_id)
        if submitted is None:
            row.value_text = None
            row.value_code = None
            row.observed_at = None
            continue
        row.value_text, row.value_code, row.observed_at = normalize_value(row, submitted, current_parameters.get(parameter_id))

    missing = missing_required_values(result)
    if payload.ready_for_validation and missing:
        raise validation_error(f"Required result parameters are missing: {', '.join(missing)}")

    previous_status = result.status
    now = datetime.now(timezone.utc)
    result.status = "RESULT_SAVED" if payload.ready_for_validation else "IN_PROCESS"
    result.saved_at = now
    result.saved_by = actor.id
    result.preliminary_at = None
    result.preliminary_by = None
    result.final_at = None
    result.final_by = None
    item.status = result.status

    if previous_status == "PRELIMINARY_VALIDATED":
        record_workflow_event(
            db,
            order_item_id=item.id,
            event_type="PRELIMINARY_INVALIDATED",
            performed_by=actor.id,
            details={"reason": "Result values were edited."},
        )
    record_workflow_event(
        db,
        order_item_id=item.id,
        event_type="RESULT_SAVED" if payload.ready_for_validation else "RESULT_IN_PROCESS",
        performed_by=actor.id,
        details={"status": result.status, "submitted_values": len(payload.values)},
    )
    record_audit(
        db,
        actor_user_id=actor.id,
        entity_type="result",
        entity_id=result.id,
        action="SAVE",
        before_data=before,
        after_data=result_snapshot(result),
    )
    db.commit()
    return result_response(db, get_order_item(db, item.id))


@router.delete("/order-items/{order_item_id}/result", status_code=status.HTTP_204_NO_CONTENT)
def delete_order_item_result(
    order_item_id: str,
    actor: User = Depends(result_writer),
    db: Session = Depends(get_db),
) -> None:
    item = get_order_item(db, order_item_id, for_update=True)
    result = get_result(db, item.id)
    if not result:
        item.status = restore_item_status_after_result_delete(item)
        db.commit()
        return None
    require_exam_area(db, item, final=result.status == "FINAL_VALIDATED", actor=actor)
    result_id = result.id
    before = result_snapshot(result)
    restored_status = restore_item_status_after_result_delete(item)
    delete_result_graph(db, result)
    item.status = restored_status
    record_workflow_event(
        db,
        order_item_id=item.id,
        event_type="RESULT_DELETED",
        performed_by=actor.id,
        details={"reason": "Resultado eliminado para correccion", "restored_status": restored_status},
    )
    record_audit(
        db,
        actor_user_id=actor.id,
        entity_type="result",
        entity_id=result_id,
        action="DELETE",
        before_data=before,
        after_data={"order_item_id": item.id, "item_status": restored_status},
    )
    db.commit()
    return None


@router.post("/order-items/{order_item_id}/result/preliminary-validation", response_model=ResultResponse)
def preliminary_validate_result(
    order_item_id: str,
    actor: User = Depends(result_writer),
    db: Session = Depends(get_db),
) -> ResultResponse:
    item = get_order_item(db, order_item_id, for_update=True)
    require_exam_area(db, item, final=False, actor=actor)
    result = require_result(db, item)
    if result.status != "RESULT_SAVED":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only a completed saved result can be preliminarily validated.")
    missing = missing_required_values(result)
    if missing:
        raise validation_error(f"Required result parameters are missing: {', '.join(missing)}")
    incomplete_ast = incomplete_ast_isolates(db, result)
    if incomplete_ast:
        raise validation_error("Antimicrobial susceptibility results are incomplete.")
    before = result_snapshot(result)
    now = datetime.now(timezone.utc)
    result.status = "PRELIMINARY_VALIDATED"
    result.preliminary_at = now
    result.preliminary_by = actor.id
    item.status = result.status
    record_workflow_event(
        db,
        order_item_id=item.id,
        event_type="PRELIMINARY_VALIDATED",
        performed_by=actor.id,
        details={"validated_at": now.isoformat()},
    )
    record_audit(
        db,
        actor_user_id=actor.id,
        entity_type="result",
        entity_id=result.id,
        action="PRELIMINARY_VALIDATE",
        before_data=before,
        after_data=result_snapshot(result),
    )
    db.commit()
    return result_response(db, get_order_item(db, item.id))


@router.post("/order-items/{order_item_id}/result/final-validation", response_model=ResultResponse)
def final_validate_result(
    order_item_id: str,
    actor: User = Depends(result_writer),
    db: Session = Depends(get_db),
) -> ResultResponse:
    item = get_order_item(db, order_item_id, for_update=True)
    require_exam_area(db, item, final=True, actor=actor)
    result = require_result(db, item)
    if result.status != "PRELIMINARY_VALIDATED":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Final validation requires a preliminary validation.")
    missing = missing_required_values(result)
    if missing:
        raise validation_error(f"Required result parameters are missing: {', '.join(missing)}")
    incomplete_ast = incomplete_ast_isolates(db, result)
    if incomplete_ast:
        raise validation_error("Antimicrobial susceptibility results are incomplete.")
    before = result_snapshot(result)
    now = datetime.now(timezone.utc)
    result.status = "FINAL_VALIDATED"
    result.final_at = now
    result.final_by = actor.id
    item.status = result.status
    record_workflow_event(
        db,
        order_item_id=item.id,
        event_type="FINAL_VALIDATED",
        performed_by=actor.id,
        details={"validated_at": now.isoformat()},
    )
    record_audit(
        db,
        actor_user_id=actor.id,
        entity_type="result",
        entity_id=result.id,
        action="FINAL_VALIDATE",
        before_data=before,
        after_data=result_snapshot(result),
    )
    db.commit()
    return result_response(db, get_order_item(db, item.id))


@router.post("/order-items/{order_item_id}/result/reopen", response_model=ResultResponse)
def reopen_result(
    order_item_id: str,
    payload: ReasonInput,
    actor: User = Depends(result_writer),
    db: Session = Depends(get_db),
) -> ResultResponse:
    item = get_order_item(db, order_item_id, for_update=True)
    result = require_result(db, item)
    if result.status not in {"PRELIMINARY_VALIDATED", "FINAL_VALIDATED"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only a validated result can be reopened.")
    previous_status = result.status
    require_exam_area(db, item, final=previous_status == "FINAL_VALIDATED", actor=actor)
    before = result_snapshot(result)
    result.status = "RESULT_SAVED"
    result.preliminary_at = None
    result.preliminary_by = None
    result.final_at = None
    result.final_by = None
    item.status = result.status
    record_workflow_event(
        db,
        order_item_id=item.id,
        event_type="RESULT_REOPENED",
        performed_by=actor.id,
        details={"reason": payload.reason, "previous_status": previous_status},
    )
    record_audit(
        db,
        actor_user_id=actor.id,
        entity_type="result",
        entity_id=result.id,
        action="REOPEN",
        before_data=before,
        after_data=result_snapshot(result),
        reason=payload.reason,
    )
    db.commit()
    return result_response(db, get_order_item(db, item.id))
