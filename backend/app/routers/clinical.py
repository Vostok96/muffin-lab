from datetime import date, datetime, time, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models import (
    AntimicrobialResult,
    Clinician,
    Destination,
    Exam,
    ExamSpecimenType,
    InstrumentMessage,
    Isolate,
    LabOrder,
    Notification,
    OrderItem,
    Origin,
    Patient,
    PrintJob,
    Result,
    ResultValue,
    Service,
    SpecimenType,
    User,
    WorkflowEvent,
)
from app.schemas import (
    CollectSpecimenInput,
    OrderCreate,
    OrderItemCreate,
    OrderItemResponse,
    OrderPage,
    OrderResponse,
    OrderUpdate,
    PatientCreate,
    PatientPage,
    PatientResponse,
    PatientUpdate,
    ReasonInput,
    ReceiveSpecimenInput,
    SpecimenDetailsUpdate,
    WorkflowEventResponse,
)
from app.services import generate_order_number, record_audit, record_workflow_event


router = APIRouter()
patient_writer = require_role("ADMIN", "PROCESS_ADMIN", "ENTRY")
order_writer = require_role("ADMIN", "PROCESS_ADMIN", "ENTRY")
specimen_collector = require_role("ADMIN", "PROCESS_ADMIN", "ENTRY", "COLLECTOR")
specimen_receiver = require_role("ADMIN", "PROCESS_ADMIN", "PROCESSOR", "COLLECTOR")
specimen_rejector = require_role("ADMIN", "PROCESS_ADMIN", "PROCESSOR")
workflow_controller = require_role("ADMIN", "PROCESS_ADMIN")


def get_entity(db: Session, model: type, entity_id: str, label: str) -> Any:
    entity = db.get(model, entity_id)
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{label} not found.")
    return entity


def get_active_entity(db: Session, model: type, entity_id: str, label: str) -> Any:
    entity = get_entity(db, model, entity_id, label)
    if not entity.is_active:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=f"{label} is inactive.")
    return entity


def ensure_not_future(value: datetime, label: str) -> None:
    if value > datetime.now(timezone.utc) + timedelta(minutes=5):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=f"{label} cannot be in the future.")


def get_order(db: Session, order_id: str, *, for_update: bool = False) -> LabOrder:
    statement = select(LabOrder).where(LabOrder.id == order_id).options(selectinload(LabOrder.items).selectinload(OrderItem.events))
    if for_update:
        statement = statement.with_for_update()
    order = db.scalar(statement)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
    return order


def get_order_item(db: Session, order_item_id: str, *, for_update: bool = False) -> OrderItem:
    statement = select(OrderItem).where(OrderItem.id == order_item_id).options(selectinload(OrderItem.events))
    if for_update:
        statement = statement.with_for_update()
    item = db.scalar(statement)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order item not found.")
    return item


def item_snapshot(item: OrderItem) -> dict[str, Any]:
    return {
        "status": item.status,
        "collection_at": item.collection_at.isoformat() if item.collection_at else None,
        "received_at": item.received_at.isoformat() if item.received_at else None,
        "destination_id": item.destination_id,
        "specimen_notes": item.specimen_notes,
        "location": item.location,
        "rejection_reason": item.rejection_reason,
    }


def commit_or_conflict(db: Session, detail: str) -> None:
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail) from error


def refresh_item(db: Session, item_id: str) -> OrderItem:
    return get_order_item(db, item_id)


def restore_item_status(item: OrderItem) -> str:
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
    for value in db.scalars(select(ResultValue).where(ResultValue.result_id == result.id)):
        db.delete(value)
    db.delete(result)


def delete_order_item_graph(db: Session, item: OrderItem) -> None:
    result = db.scalar(select(Result).where(Result.order_item_id == item.id))
    if result:
        delete_result_graph(db, result)
    for print_job in db.scalars(select(PrintJob).where(PrintJob.order_item_id == item.id)):
        db.delete(print_job)
    for notification in db.scalars(select(Notification).where(Notification.order_item_id == item.id)):
        db.delete(notification)
    for message in db.scalars(select(InstrumentMessage).where(InstrumentMessage.order_item_id == item.id)):
        message.order_item_id = None
    for event in db.scalars(select(WorkflowEvent).where(WorkflowEvent.order_item_id == item.id)):
        db.delete(event)
    db.delete(item)


@router.get("/patients", tags=["Patients"], response_model=PatientPage)
def list_patients(
    search: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PatientPage:
    filters = []
    if search:
        term = f"%{search.strip()}%"
        filters.append(
            or_(
                Patient.medical_record_number.ilike(term),
                Patient.document_number.ilike(term),
                Patient.family_name.ilike(term),
                Patient.given_name.ilike(term),
            )
        )
    total = db.scalar(select(func.count()).select_from(Patient).where(*filters)) or 0
    patients = list(
        db.scalars(
            select(Patient)
            .where(*filters)
            .order_by(Patient.family_name, Patient.given_name, Patient.medical_record_number)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    return PatientPage(
        data=[PatientResponse.model_validate(patient) for patient in patients],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.post("/patients", tags=["Patients"], response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
def create_patient(payload: PatientCreate, actor: User = Depends(patient_writer), db: Session = Depends(get_db)) -> Patient:
    medical_record_number = payload.medical_record_number.upper()
    document_number = payload.document_number.upper() if payload.document_number else None
    if db.scalar(select(Patient).where(Patient.medical_record_number == medical_record_number)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Medical record number already exists.")
    if document_number and db.scalar(select(Patient).where(Patient.document_number == document_number)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Document number already exists.")
    patient = Patient(
        **(
            payload.model_dump()
            | {"medical_record_number": medical_record_number, "document_number": document_number}
        )
    )
    db.add(patient)
    db.flush()
    record_audit(
        db,
        actor_user_id=actor.id,
        entity_type="patient",
        entity_id=patient.id,
        action="CREATE",
        after_data={"medical_record_number": patient.medical_record_number},
    )
    commit_or_conflict(db, "Patient identifiers conflict with an existing record.")
    db.refresh(patient)
    return patient


@router.get("/patients/{patient_id}", tags=["Patients"], response_model=PatientResponse)
def get_patient(patient_id: str, _: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Patient:
    return get_entity(db, Patient, patient_id, "Patient")


@router.patch("/patients/{patient_id}", tags=["Patients"], response_model=PatientResponse)
def update_patient(
    patient_id: str,
    payload: PatientUpdate,
    actor: User = Depends(patient_writer),
    db: Session = Depends(get_db),
) -> Patient:
    patient = get_entity(db, Patient, patient_id, "Patient")
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="At least one field must be provided.")
    for required_field in ("medical_record_number", "family_name", "given_name", "birth_date", "sex"):
        if required_field in changes and changes[required_field] is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=f"{required_field} cannot be null.")
    if "medical_record_number" in changes:
        changes["medical_record_number"] = changes["medical_record_number"].upper()
        duplicate = db.scalar(
            select(Patient).where(
                Patient.medical_record_number == changes["medical_record_number"],
                Patient.id != patient.id,
            )
        )
        if duplicate:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Medical record number already exists.")
    if changes.get("document_number"):
        changes["document_number"] = changes["document_number"].upper()
        duplicate = db.scalar(
            select(Patient).where(Patient.document_number == changes["document_number"], Patient.id != patient.id)
        )
        if duplicate:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Document number already exists.")
    before = {field: getattr(patient, field) for field in changes}
    for field, value in changes.items():
        setattr(patient, field, value)
    record_audit(
        db,
        actor_user_id=actor.id,
        entity_type="patient",
        entity_id=patient.id,
        action="UPDATE",
        before_data={key: value.isoformat() if isinstance(value, date) else value for key, value in before.items()},
        after_data={key: value.isoformat() if isinstance(value, date) else value for key, value in changes.items()},
    )
    commit_or_conflict(db, "Patient identifiers conflict with an existing record.")
    db.refresh(patient)
    return patient


@router.delete("/patients/{patient_id}", tags=["Patients"], status_code=status.HTTP_204_NO_CONTENT)
def delete_patient(patient_id: str, actor: User = Depends(patient_writer), db: Session = Depends(get_db)) -> None:
    patient = get_entity(db, Patient, patient_id, "Patient")
    finalized_item = db.scalar(
        select(OrderItem.id)
        .join(LabOrder, LabOrder.id == OrderItem.lab_order_id)
        .outerjoin(Result, Result.order_item_id == OrderItem.id)
        .where(
            LabOrder.patient_id == patient.id,
            or_(OrderItem.status == "FINAL_VALIDATED", Result.status == "FINAL_VALIDATED"),
        )
        .limit(1)
    )
    if finalized_item:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Patients with final validated results cannot be deleted.",
        )

    orders = list(
        db.scalars(
            select(LabOrder)
            .where(LabOrder.patient_id == patient.id)
            .options(selectinload(LabOrder.items))
        ).unique()
    )
    before = {
        "medical_record_number": patient.medical_record_number,
        "document_number": patient.document_number,
        "family_name": patient.family_name,
        "given_name": patient.given_name,
        "orders": len(orders),
        "items": sum(len(order.items) for order in orders),
    }
    for order in orders:
        for item in list(order.items):
            delete_order_item_graph(db, item)
        db.delete(order)
    db.delete(patient)
    record_audit(
        db,
        actor_user_id=actor.id,
        entity_type="patient",
        entity_id=patient_id,
        action="DELETE",
        before_data=before,
        after_data={"deleted": True},
    )
    commit_or_conflict(db, "Patient cannot be deleted because it is referenced by protected records.")
    return None


@router.get("/orders", tags=["Orders"], response_model=OrderPage)
def list_orders(
    date_from: date | None = Query(default=None, alias="from"),
    date_to: date | None = Query(default=None, alias="to"),
    search: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrderPage:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="from cannot be after to.")
    filters = []
    if date_from:
        filters.append(LabOrder.ordered_at >= datetime.combine(date_from, time.min, tzinfo=timezone.utc))
    if date_to:
        filters.append(LabOrder.ordered_at < datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=timezone.utc))
    if search:
        term = f"%{search.strip()}%"
        filters.append(
            or_(
                LabOrder.order_number.ilike(term),
                Patient.medical_record_number.ilike(term),
                Patient.document_number.ilike(term),
                Patient.family_name.ilike(term),
                Patient.given_name.ilike(term),
            )
        )
    count_statement = select(func.count()).select_from(LabOrder).join(Patient).where(*filters)
    total = db.scalar(count_statement) or 0
    orders = list(
        db.scalars(
            select(LabOrder)
            .join(Patient)
            .where(*filters)
            .options(selectinload(LabOrder.items).selectinload(OrderItem.events))
            .order_by(LabOrder.ordered_at.desc(), LabOrder.order_number.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).unique()
    )
    return OrderPage(
        data=[OrderResponse.model_validate(order) for order in orders],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.post("/orders", tags=["Orders"], response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(payload: OrderCreate, actor: User = Depends(order_writer), db: Session = Depends(get_db)) -> LabOrder:
    ensure_not_future(payload.ordered_at, "ordered_at")
    get_entity(db, Patient, payload.patient_id, "Patient")
    get_active_entity(db, Origin, payload.origin_id, "Origin")
    get_active_entity(db, Service, payload.service_id, "Service")
    if payload.clinician_id:
        get_active_entity(db, Clinician, payload.clinician_id, "Clinician")
    order = LabOrder(
        **payload.model_dump(),
        order_number=generate_order_number(db, payload.ordered_at),
        status="REGISTERED",
    )
    db.add(order)
    db.flush()
    record_audit(
        db,
        actor_user_id=actor.id,
        entity_type="lab_order",
        entity_id=order.id,
        action="CREATE",
        after_data={"order_number": order.order_number, "patient_id": order.patient_id},
    )
    commit_or_conflict(db, "Order number conflicts with an existing record.")
    return get_order(db, order.id)


@router.get("/orders/{order_id}", tags=["Orders"], response_model=OrderResponse)
def get_order_detail(order_id: str, _: User = Depends(get_current_user), db: Session = Depends(get_db)) -> LabOrder:
    return get_order(db, order_id)


@router.patch("/orders/{order_id}", tags=["Orders"], response_model=OrderResponse)
def update_order(
    order_id: str,
    payload: OrderUpdate,
    actor: User = Depends(order_writer),
    db: Session = Depends(get_db),
) -> LabOrder:
    order = get_order(db, order_id, for_update=True)
    if order.status not in {"DRAFT", "REGISTERED"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only draft or registered orders can be updated.")
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="At least one field must be provided.")
    for field in ("ordered_at", "origin_id", "service_id"):
        if field in changes and changes[field] is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=f"{field} cannot be null.")
    if "ordered_at" in changes:
        ensure_not_future(changes["ordered_at"], "ordered_at")
    if "origin_id" in changes:
        get_active_entity(db, Origin, changes["origin_id"], "Origin")
    if "service_id" in changes:
        get_active_entity(db, Service, changes["service_id"], "Service")
    if changes.get("clinician_id"):
        get_active_entity(db, Clinician, changes["clinician_id"], "Clinician")
    before = {field: getattr(order, field) for field in changes}
    for field, value in changes.items():
        setattr(order, field, value)
    record_audit(
        db,
        actor_user_id=actor.id,
        entity_type="lab_order",
        entity_id=order.id,
        action="UPDATE",
        before_data={key: value.isoformat() if isinstance(value, datetime) else value for key, value in before.items()},
        after_data={key: value.isoformat() if isinstance(value, datetime) else value for key, value in changes.items()},
    )
    db.commit()
    return get_order(db, order.id)


@router.post("/orders/{order_id}/items", tags=["Orders"], response_model=OrderItemResponse, status_code=status.HTTP_201_CREATED)
def add_order_item(
    order_id: str,
    payload: OrderItemCreate,
    actor: User = Depends(order_writer),
    db: Session = Depends(get_db),
) -> OrderItem:
    order = get_order(db, order_id, for_update=True)
    if order.status not in {"DRAFT", "REGISTERED"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Items cannot be added to this order.")
    exam = get_active_entity(db, Exam, payload.exam_id, "Exam")
    specimen_type = get_active_entity(db, SpecimenType, payload.specimen_type_id, "Specimen type")
    if not specimen_type.is_selectable:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="A terminal specimen type must be selected.")
    if not db.get(ExamSpecimenType, (payload.exam_id, payload.specimen_type_id)):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Specimen type is not allowed for this exam.")
    if payload.collection_at:
        ensure_not_future(payload.collection_at, "collection_at")
    item_number = (db.scalar(select(func.max(OrderItem.item_number)).where(OrderItem.lab_order_id == order.id)) or 0) + 1
    suffix = exam.barcode_suffix or exam.code[:8]
    barcode = f"{order.order_number.replace('-', '')}-{item_number:02d}-{suffix}".upper()
    item = OrderItem(
        lab_order=order,
        item_number=item_number,
        exam_id=payload.exam_id,
        specimen_type_id=payload.specimen_type_id,
        barcode=barcode,
        collection_at=payload.collection_at,
        specimen_notes=payload.specimen_notes,
        location=payload.location,
        status="COLLECTED" if payload.collection_at else "REGISTERED",
    )
    db.add(item)
    db.flush()
    record_workflow_event(
        db,
        order_item_id=item.id,
        event_type="REGISTERED",
        performed_by=actor.id,
        details={"order_number": order.order_number, "barcode": item.barcode},
    )
    if payload.collection_at:
        record_workflow_event(
            db,
            order_item_id=item.id,
            event_type="COLLECTED",
            performed_by=actor.id,
            details={"collection_at": payload.collection_at.isoformat(), "location": payload.location},
        )
    record_audit(
        db,
        actor_user_id=actor.id,
        entity_type="order_item",
        entity_id=item.id,
        action="CREATE",
        after_data={"order_id": order.id, "barcode": item.barcode, "status": item.status},
    )
    commit_or_conflict(db, "Order item number or barcode conflicts with an existing record.")
    return refresh_item(db, item.id)


@router.post("/order-items/{order_item_id}/collect", tags=["Orders"], response_model=OrderItemResponse)
def collect_specimen(
    order_item_id: str,
    payload: CollectSpecimenInput,
    actor: User = Depends(specimen_collector),
    db: Session = Depends(get_db),
) -> OrderItem:
    item = get_order_item(db, order_item_id, for_update=True)
    if item.status != "REGISTERED":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only registered specimens can be collected.")
    ensure_not_future(payload.collection_at, "collection_at")
    before = item_snapshot(item)
    item.collection_at = payload.collection_at
    item.status = "COLLECTED"
    if payload.specimen_notes is not None:
        item.specimen_notes = payload.specimen_notes
    if payload.location is not None:
        item.location = payload.location
    record_workflow_event(
        db,
        order_item_id=item.id,
        event_type="COLLECTED",
        performed_by=actor.id,
        details={"collection_at": item.collection_at.isoformat(), "location": item.location},
    )
    record_audit(db, actor_user_id=actor.id, entity_type="order_item", entity_id=item.id, action="COLLECT", before_data=before, after_data=item_snapshot(item))
    db.commit()
    return refresh_item(db, item.id)


@router.post("/order-items/{order_item_id}/receive", tags=["Orders"], response_model=OrderItemResponse)
def receive_specimen(
    order_item_id: str,
    payload: ReceiveSpecimenInput,
    actor: User = Depends(specimen_receiver),
    db: Session = Depends(get_db),
) -> OrderItem:
    item = get_order_item(db, order_item_id, for_update=True)
    if item.status not in {"REGISTERED", "COLLECTED"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Specimen cannot be received from its current status.")
    destination = get_active_entity(db, Destination, payload.destination_id, "Destination")
    collection_at = payload.collection_at or item.collection_at
    if collection_at is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="collection_at is required before reception.")
    ensure_not_future(collection_at, "collection_at")
    ensure_not_future(payload.received_at, "received_at")
    if payload.received_at < collection_at:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="received_at cannot be before collection_at.")
    before = item_snapshot(item)
    if item.collection_at is None:
        item.collection_at = collection_at
        record_workflow_event(
            db,
            order_item_id=item.id,
            event_type="COLLECTED",
            performed_by=actor.id,
            details={"collection_at": collection_at.isoformat(), "recorded_during_reception": True},
        )
    item.received_at = payload.received_at
    item.destination_id = destination.id
    item.status = "RECEIVED"
    if payload.specimen_notes is not None:
        item.specimen_notes = payload.specimen_notes
    if payload.location is not None:
        item.location = payload.location
    record_workflow_event(
        db,
        order_item_id=item.id,
        event_type="RECEIVED",
        performed_by=actor.id,
        details={"received_at": item.received_at.isoformat(), "destination_id": destination.id},
    )
    record_audit(db, actor_user_id=actor.id, entity_type="order_item", entity_id=item.id, action="RECEIVE", before_data=before, after_data=item_snapshot(item))
    db.commit()
    return refresh_item(db, item.id)


@router.patch("/order-items/{order_item_id}/specimen-details", tags=["Orders"], response_model=OrderItemResponse)
def update_specimen_details(
    order_item_id: str,
    payload: SpecimenDetailsUpdate,
    actor: User = Depends(specimen_receiver),
    db: Session = Depends(get_db),
) -> OrderItem:
    item = get_order_item(db, order_item_id, for_update=True)
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="At least one field must be provided.")
    if "collection_at" in changes and changes["collection_at"] is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="collection_at cannot be null.")
    if "received_at" in changes and changes["received_at"] is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="received_at cannot be null.")

    effective_collection = changes.get("collection_at", item.collection_at)
    effective_reception = changes.get("received_at", item.received_at)
    if effective_collection:
        ensure_not_future(effective_collection, "collection_at")
    if effective_reception:
        ensure_not_future(effective_reception, "received_at")
        if not effective_collection:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="collection_at is required before reception.")
        if effective_reception < effective_collection:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="received_at cannot be before collection_at.")

    before = item_snapshot(item)
    if all(getattr(item, field) == value for field, value in changes.items()):
        return item
    if item.status in {"PRELIMINARY_VALIDATED", "FINAL_VALIDATED", "REJECTED", "CANCELLED"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Validated, rejected, or cancelled specimens cannot be corrected.",
        )
    for field, value in changes.items():
        setattr(item, field, value)
    after = item_snapshot(item)
    record_workflow_event(
        db,
        order_item_id=item.id,
        event_type="SPECIMEN_DETAILS_CORRECTED",
        performed_by=actor.id,
        details={"before": before, "after": after},
    )
    record_audit(
        db,
        actor_user_id=actor.id,
        entity_type="order_item",
        entity_id=item.id,
        action="CORRECT_SPECIMEN_DETAILS",
        before_data=before,
        after_data=after,
    )
    db.commit()
    return refresh_item(db, item.id)


@router.post("/order-items/{order_item_id}/reject", tags=["Orders"], response_model=OrderItemResponse)
def reject_specimen(
    order_item_id: str,
    payload: ReasonInput,
    actor: User = Depends(specimen_rejector),
    db: Session = Depends(get_db),
) -> OrderItem:
    item = get_order_item(db, order_item_id, for_update=True)
    if item.status not in {"REGISTERED", "COLLECTED", "RECEIVED"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Specimen cannot be rejected from its current status.")
    before = item_snapshot(item)
    item.status = "REJECTED"
    item.rejection_reason = payload.reason
    record_workflow_event(db, order_item_id=item.id, event_type="REJECTED", performed_by=actor.id, details={"reason": payload.reason})
    record_audit(db, actor_user_id=actor.id, entity_type="order_item", entity_id=item.id, action="REJECT", before_data=before, after_data=item_snapshot(item), reason=payload.reason)
    db.commit()
    return refresh_item(db, item.id)


@router.post("/order-items/{order_item_id}/cancel", tags=["Orders"], response_model=OrderItemResponse)
def cancel_order_item(
    order_item_id: str,
    payload: ReasonInput,
    actor: User = Depends(order_writer),
    db: Session = Depends(get_db),
) -> OrderItem:
    item = get_order_item(db, order_item_id, for_update=True)
    if item.status not in {"REGISTERED", "COLLECTED", "RECEIVED"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Order item cannot be cancelled from its current status.")
    before = item_snapshot(item)
    item.status = "CANCELLED"
    record_workflow_event(db, order_item_id=item.id, event_type="CANCELLED", performed_by=actor.id, details={"reason": payload.reason})
    record_audit(db, actor_user_id=actor.id, entity_type="order_item", entity_id=item.id, action="CANCEL", before_data=before, after_data=item_snapshot(item), reason=payload.reason)
    db.commit()
    return refresh_item(db, item.id)


@router.post("/order-items/{order_item_id}/reopen", tags=["Orders"], response_model=OrderItemResponse)
def reopen_order_item(
    order_item_id: str,
    payload: ReasonInput,
    actor: User = Depends(workflow_controller),
    db: Session = Depends(get_db),
) -> OrderItem:
    item = get_order_item(db, order_item_id, for_update=True)
    if item.status not in {"CANCELLED", "REJECTED"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only cancelled or rejected items can be reopened.")
    before = item_snapshot(item)
    item.status = restore_item_status(item)
    item.rejection_reason = None
    record_workflow_event(
        db,
        order_item_id=item.id,
        event_type="REOPENED",
        performed_by=actor.id,
        details={"reason": payload.reason, "restored_status": item.status},
    )
    record_audit(db, actor_user_id=actor.id, entity_type="order_item", entity_id=item.id, action="REOPEN", before_data=before, after_data=item_snapshot(item), reason=payload.reason)
    db.commit()
    return refresh_item(db, item.id)


@router.post("/orders/{order_id}/cancel", tags=["Orders"], response_model=OrderResponse)
def cancel_order(
    order_id: str,
    payload: ReasonInput,
    actor: User = Depends(order_writer),
    db: Session = Depends(get_db),
) -> LabOrder:
    order = get_order(db, order_id, for_update=True)
    if order.status not in {"DRAFT", "REGISTERED"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Order cannot be cancelled from its current status.")
    forbidden = [item for item in order.items if item.status not in {"REGISTERED", "COLLECTED", "RECEIVED", "REJECTED", "CANCELLED"}]
    if forbidden:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Order contains items that have already entered result processing.")
    order.status = "CANCELLED"
    for item in order.items:
        if item.status in {"REGISTERED", "COLLECTED", "RECEIVED"}:
            before = item_snapshot(item)
            item.status = "CANCELLED"
            record_workflow_event(db, order_item_id=item.id, event_type="CANCELLED", performed_by=actor.id, details={"reason": payload.reason, "order_cancelled": True})
            record_audit(db, actor_user_id=actor.id, entity_type="order_item", entity_id=item.id, action="CANCEL", before_data=before, after_data=item_snapshot(item), reason=payload.reason)
    record_audit(db, actor_user_id=actor.id, entity_type="lab_order", entity_id=order.id, action="CANCEL", before_data={"status": "REGISTERED"}, after_data={"status": order.status}, reason=payload.reason)
    db.commit()
    return get_order(db, order.id)


@router.post("/orders/{order_id}/reopen", tags=["Orders"], response_model=OrderResponse)
def reopen_order(
    order_id: str,
    payload: ReasonInput,
    actor: User = Depends(workflow_controller),
    db: Session = Depends(get_db),
) -> LabOrder:
    order = get_order(db, order_id, for_update=True)
    if order.status != "CANCELLED":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only cancelled orders can be reopened.")
    order.status = "REGISTERED"
    for item in order.items:
        if item.status == "CANCELLED":
            before = item_snapshot(item)
            item.status = restore_item_status(item)
            record_workflow_event(
                db,
                order_item_id=item.id,
                event_type="REOPENED",
                performed_by=actor.id,
                details={"reason": payload.reason, "order_reopened": True, "restored_status": item.status},
            )
            record_audit(db, actor_user_id=actor.id, entity_type="order_item", entity_id=item.id, action="REOPEN", before_data=before, after_data=item_snapshot(item), reason=payload.reason)
    record_audit(db, actor_user_id=actor.id, entity_type="lab_order", entity_id=order.id, action="REOPEN", before_data={"status": "CANCELLED"}, after_data={"status": order.status}, reason=payload.reason)
    db.commit()
    return get_order(db, order.id)


@router.get("/order-items/{order_item_id}/events", tags=["Orders"], response_model=list[WorkflowEventResponse])
def list_workflow_events(
    order_item_id: str,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[WorkflowEvent]:
    get_entity(db, OrderItem, order_item_id, "Order item")
    return list(
        db.scalars(
            select(WorkflowEvent)
            .where(WorkflowEvent.order_item_id == order_item_id)
            .order_by(WorkflowEvent.occurred_at, WorkflowEvent.id)
        )
    )
