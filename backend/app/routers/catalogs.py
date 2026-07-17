from datetime import datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models import (
    Clinician,
    Container,
    Destination,
    Exam,
    ExamParameter,
    ExamSpecimenType,
    LaboratoryArea,
    Origin,
    ParameterDefinition,
    Service,
    SpecimenType,
    User,
)
from app.schemas import (
    CatalogCreate,
    CatalogPage,
    CatalogResponse,
    CatalogUpdate,
    ClinicianCreate,
    ClinicianResponse,
    ClinicianUpdate,
    ExamCreate,
    ExamParameterInput,
    ExamParameterResponse,
    ExamResponse,
    ExamSpecimenTypeInput,
    ExamSpecimenTypeResponse,
    ExamUpdate,
    LaboratoryAreaCreate,
    LaboratoryAreaResponse,
    LaboratoryAreaUpdate,
    ParameterDefinitionCreate,
    ParameterDefinitionResponse,
    ParameterDefinitionUpdate,
    SpecimenTypeCreate,
    SpecimenTypeResponse,
    SpecimenTypeUpdate,
)
from app.services import record_audit


router = APIRouter(prefix="/catalogs", tags=["Catalogs"])
catalog_writer = require_role("ADMIN", "PROCESS_ADMIN")


def json_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return value


def snapshot(entity: Any) -> dict[str, Any]:
    return {column.name: json_value(getattr(entity, column.name)) for column in entity.__table__.columns}


def ensure_patch(data: dict[str, Any]) -> None:
    if not data:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="At least one field must be provided.")


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


def commit_catalog_change(
    db: Session,
    actor: User,
    entity: Any,
    entity_type: str,
    action: str,
    before_data: dict[str, Any] | None = None,
) -> None:
    try:
        db.flush()
        record_audit(
            db,
            actor_user_id=actor.id,
            entity_type=entity_type,
            entity_id=entity.id,
            action=action,
            before_data=before_data,
            after_data=snapshot(entity),
        )
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Catalog values conflict with an existing record.") from error


def create_catalog_entity(db: Session, model: type, payload: Any, actor: User, entity_type: str) -> Any:
    data = payload.model_dump()
    data["code"] = data["code"].upper()
    if db.scalar(select(model).where(model.code == data["code"])):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Catalog code already exists.")
    entity = model(**data)
    db.add(entity)
    commit_catalog_change(db, actor, entity, entity_type, "CREATE")
    db.refresh(entity)
    return entity


def update_catalog_entity(db: Session, entity: Any, payload: Any, actor: User, entity_type: str) -> Any:
    data = payload.model_dump(exclude_unset=True)
    ensure_patch(data)
    if "code" in data:
        if data["code"] is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="code cannot be null.")
        data["code"] = data["code"].upper()
        duplicate = db.scalar(
            select(entity.__class__).where(entity.__class__.code == data["code"], entity.__class__.id != entity.id)
        )
        if duplicate:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Catalog code already exists.")
    if "name" in data and data["name"] is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="name cannot be null.")
    before = snapshot(entity)
    for key, value in data.items():
        setattr(entity, key, value)
    commit_catalog_change(db, actor, entity, entity_type, "UPDATE", before)
    db.refresh(entity)
    return entity


def list_catalog_page(
    db: Session,
    model: type,
    response_model: type,
    active_only: bool,
    search: str | None,
    page: int,
    page_size: int,
    search_fields: tuple[str, ...] = ("code", "name"),
) -> CatalogPage:
    filters = []
    if active_only:
        filters.append(model.is_active.is_(True))
    if search:
        term = f"%{search.strip()}%"
        filters.append(or_(*(getattr(model, field).ilike(term) for field in search_fields)))
    total = db.scalar(select(func.count()).select_from(model).where(*filters)) or 0
    items = list(
        db.scalars(
            select(model)
            .where(*filters)
            .order_by(model.code)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    return CatalogPage(
        data=[response_model.model_validate(item) for item in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/areas", response_model=CatalogPage[LaboratoryAreaResponse])
def list_areas(
    active_only: bool = True,
    search: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CatalogPage[LaboratoryAreaResponse]:
    return list_catalog_page(db, LaboratoryArea, LaboratoryAreaResponse, active_only, search, page, page_size)


@router.post("/areas", response_model=LaboratoryAreaResponse, status_code=status.HTTP_201_CREATED)
def create_area(payload: LaboratoryAreaCreate, actor: User = Depends(catalog_writer), db: Session = Depends(get_db)) -> LaboratoryArea:
    return create_catalog_entity(db, LaboratoryArea, payload, actor, "laboratory_area")


@router.patch("/areas/{area_id}", response_model=LaboratoryAreaResponse)
def update_area(area_id: str, payload: LaboratoryAreaUpdate, actor: User = Depends(catalog_writer), db: Session = Depends(get_db)) -> LaboratoryArea:
    return update_catalog_entity(db, get_entity(db, LaboratoryArea, area_id, "Laboratory area"), payload, actor, "laboratory_area")


@router.get("/origins", response_model=CatalogPage[CatalogResponse])
def list_origins(
    active_only: bool = True,
    search: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CatalogPage[CatalogResponse]:
    return list_catalog_page(db, Origin, CatalogResponse, active_only, search, page, page_size)


@router.post("/origins", response_model=CatalogResponse, status_code=status.HTTP_201_CREATED)
def create_origin(payload: CatalogCreate, actor: User = Depends(catalog_writer), db: Session = Depends(get_db)) -> Origin:
    return create_catalog_entity(db, Origin, payload, actor, "origin")


@router.patch("/origins/{origin_id}", response_model=CatalogResponse)
def update_origin(origin_id: str, payload: CatalogUpdate, actor: User = Depends(catalog_writer), db: Session = Depends(get_db)) -> Origin:
    return update_catalog_entity(db, get_entity(db, Origin, origin_id, "Origin"), payload, actor, "origin")


@router.get("/services", response_model=CatalogPage[CatalogResponse])
def list_services(
    active_only: bool = True,
    search: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CatalogPage[CatalogResponse]:
    return list_catalog_page(db, Service, CatalogResponse, active_only, search, page, page_size)


@router.post("/services", response_model=CatalogResponse, status_code=status.HTTP_201_CREATED)
def create_service(payload: CatalogCreate, actor: User = Depends(catalog_writer), db: Session = Depends(get_db)) -> Service:
    return create_catalog_entity(db, Service, payload, actor, "service")


@router.patch("/services/{service_id}", response_model=CatalogResponse)
def update_service(service_id: str, payload: CatalogUpdate, actor: User = Depends(catalog_writer), db: Session = Depends(get_db)) -> Service:
    return update_catalog_entity(db, get_entity(db, Service, service_id, "Service"), payload, actor, "service")


@router.get("/clinicians", response_model=CatalogPage[ClinicianResponse])
def list_clinicians(
    active_only: bool = True,
    search: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CatalogPage[ClinicianResponse]:
    return list_catalog_page(
        db,
        Clinician,
        ClinicianResponse,
        active_only,
        search,
        page,
        page_size,
        ("code", "family_name", "given_name", "email"),
    )


@router.post("/clinicians", response_model=ClinicianResponse, status_code=status.HTTP_201_CREATED)
def create_clinician(payload: ClinicianCreate, actor: User = Depends(catalog_writer), db: Session = Depends(get_db)) -> Clinician:
    return create_catalog_entity(db, Clinician, payload, actor, "clinician")


@router.patch("/clinicians/{clinician_id}", response_model=ClinicianResponse)
def update_clinician(clinician_id: str, payload: ClinicianUpdate, actor: User = Depends(catalog_writer), db: Session = Depends(get_db)) -> Clinician:
    return update_catalog_entity(db, get_entity(db, Clinician, clinician_id, "Clinician"), payload, actor, "clinician")


@router.get("/containers", response_model=CatalogPage[CatalogResponse])
def list_containers(
    active_only: bool = True,
    search: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CatalogPage[CatalogResponse]:
    return list_catalog_page(db, Container, CatalogResponse, active_only, search, page, page_size)


@router.post("/containers", response_model=CatalogResponse, status_code=status.HTTP_201_CREATED)
def create_container(payload: CatalogCreate, actor: User = Depends(catalog_writer), db: Session = Depends(get_db)) -> Container:
    return create_catalog_entity(db, Container, payload, actor, "container")


@router.patch("/containers/{container_id}", response_model=CatalogResponse)
def update_container(container_id: str, payload: CatalogUpdate, actor: User = Depends(catalog_writer), db: Session = Depends(get_db)) -> Container:
    return update_catalog_entity(db, get_entity(db, Container, container_id, "Container"), payload, actor, "container")


@router.get("/destinations", response_model=CatalogPage[CatalogResponse])
def list_destinations(
    active_only: bool = True,
    search: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CatalogPage[CatalogResponse]:
    return list_catalog_page(db, Destination, CatalogResponse, active_only, search, page, page_size)


@router.post("/destinations", response_model=CatalogResponse, status_code=status.HTTP_201_CREATED)
def create_destination(payload: CatalogCreate, actor: User = Depends(catalog_writer), db: Session = Depends(get_db)) -> Destination:
    return create_catalog_entity(db, Destination, payload, actor, "destination")


@router.patch("/destinations/{destination_id}", response_model=CatalogResponse)
def update_destination(
    destination_id: str,
    payload: CatalogUpdate,
    actor: User = Depends(catalog_writer),
    db: Session = Depends(get_db),
) -> Destination:
    return update_catalog_entity(db, get_entity(db, Destination, destination_id, "Destination"), payload, actor, "destination")


@router.get("/specimen-types", response_model=CatalogPage[SpecimenTypeResponse])
def list_specimen_types(
    active_only: bool = True,
    search: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CatalogPage[SpecimenTypeResponse]:
    return list_catalog_page(db, SpecimenType, SpecimenTypeResponse, active_only, search, page, page_size)


@router.post("/specimen-types", response_model=SpecimenTypeResponse, status_code=status.HTTP_201_CREATED)
def create_specimen_type(payload: SpecimenTypeCreate, actor: User = Depends(catalog_writer), db: Session = Depends(get_db)) -> SpecimenType:
    get_active_entity(db, Container, payload.container_id, "Container")
    if payload.parent_id:
        parent = get_active_entity(db, SpecimenType, payload.parent_id, "Parent specimen type")
        if parent.parent_id is not None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Specimen hierarchy supports only levels 1 and 2.")
    return create_catalog_entity(db, SpecimenType, payload, actor, "specimen_type")


@router.patch("/specimen-types/{specimen_type_id}", response_model=SpecimenTypeResponse)
def update_specimen_type(
    specimen_type_id: str,
    payload: SpecimenTypeUpdate,
    actor: User = Depends(catalog_writer),
    db: Session = Depends(get_db),
) -> SpecimenType:
    if "container_id" in payload.model_fields_set:
        if payload.container_id is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="container_id cannot be null.")
        get_active_entity(db, Container, payload.container_id, "Container")
    if "parent_id" in payload.model_fields_set and payload.parent_id:
        parent = get_active_entity(db, SpecimenType, payload.parent_id, "Parent specimen type")
        if parent.id == specimen_type_id or parent.parent_id is not None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Invalid specimen hierarchy parent.")
    return update_catalog_entity(db, get_entity(db, SpecimenType, specimen_type_id, "Specimen type"), payload, actor, "specimen_type")


@router.get("/exams", response_model=CatalogPage[ExamResponse])
def list_exams(
    active_only: bool = True,
    search: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CatalogPage[ExamResponse]:
    return list_catalog_page(db, Exam, ExamResponse, active_only, search, page, page_size)


@router.post("/exams", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
def create_exam(payload: ExamCreate, actor: User = Depends(catalog_writer), db: Session = Depends(get_db)) -> Exam:
    get_active_entity(db, LaboratoryArea, payload.laboratory_area_id, "Laboratory area")
    if payload.external_code and db.scalar(select(Exam).where(Exam.external_code == payload.external_code)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Exam external_code already exists.")
    return create_catalog_entity(db, Exam, payload, actor, "exam")


@router.patch("/exams/{exam_id}", response_model=ExamResponse)
def update_exam(exam_id: str, payload: ExamUpdate, actor: User = Depends(catalog_writer), db: Session = Depends(get_db)) -> Exam:
    if "laboratory_area_id" in payload.model_fields_set:
        if payload.laboratory_area_id is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="laboratory_area_id cannot be null.")
        get_active_entity(db, LaboratoryArea, payload.laboratory_area_id, "Laboratory area")
    exam = get_entity(db, Exam, exam_id, "Exam")
    if payload.external_code and db.scalar(
        select(Exam).where(Exam.external_code == payload.external_code, Exam.id != exam.id)
    ):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Exam external_code already exists.")
    return update_catalog_entity(db, exam, payload, actor, "exam")


@router.get("/parameters", response_model=CatalogPage[ParameterDefinitionResponse])
def list_parameters(
    active_only: bool = True,
    search: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CatalogPage[ParameterDefinitionResponse]:
    return list_catalog_page(db, ParameterDefinition, ParameterDefinitionResponse, active_only, search, page, page_size)


@router.post("/parameters", response_model=ParameterDefinitionResponse, status_code=status.HTTP_201_CREATED)
def create_parameter(
    payload: ParameterDefinitionCreate,
    actor: User = Depends(catalog_writer),
    db: Session = Depends(get_db),
) -> ParameterDefinition:
    return create_catalog_entity(db, ParameterDefinition, payload, actor, "parameter_definition")


@router.patch("/parameters/{parameter_id}", response_model=ParameterDefinitionResponse)
def update_parameter(
    parameter_id: str,
    payload: ParameterDefinitionUpdate,
    actor: User = Depends(catalog_writer),
    db: Session = Depends(get_db),
) -> ParameterDefinition:
    entity = get_entity(db, ParameterDefinition, parameter_id, "Parameter")
    changes = payload.model_dump(exclude_unset=True)
    ensure_patch(changes)
    complete = {field: getattr(entity, field) for field in ParameterDefinitionCreate.model_fields}
    complete.update(changes)
    validated = ParameterDefinitionCreate.model_validate(complete)
    return update_catalog_entity(db, entity, validated, actor, "parameter_definition")


@router.get("/exams/{exam_id}/specimen-types", response_model=list[ExamSpecimenTypeResponse])
def list_exam_specimen_types(
    exam_id: str,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ExamSpecimenType]:
    get_entity(db, Exam, exam_id, "Exam")
    return list(db.scalars(select(ExamSpecimenType).where(ExamSpecimenType.exam_id == exam_id).order_by(ExamSpecimenType.specimen_type_id)))


@router.put("/exams/{exam_id}/specimen-types/{specimen_type_id}", response_model=ExamSpecimenTypeResponse)
def set_exam_specimen_type(
    exam_id: str,
    specimen_type_id: str,
    payload: ExamSpecimenTypeInput,
    actor: User = Depends(catalog_writer),
    db: Session = Depends(get_db),
) -> ExamSpecimenType:
    get_active_entity(db, Exam, exam_id, "Exam")
    get_active_entity(db, SpecimenType, specimen_type_id, "Specimen type")
    link = db.get(ExamSpecimenType, (exam_id, specimen_type_id))
    before = snapshot(link) if link else None
    if link:
        link.is_favorite = payload.is_favorite
        action = "UPDATE"
    else:
        link = ExamSpecimenType(exam_id=exam_id, specimen_type_id=specimen_type_id, is_favorite=payload.is_favorite)
        db.add(link)
        action = "CREATE"
    try:
        db.flush()
        record_audit(
            db,
            actor_user_id=actor.id,
            entity_type="exam_specimen_type",
            entity_id=exam_id,
            action=action,
            before_data=before,
            after_data=snapshot(link),
        )
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Exam-specimen relation conflicts with an existing record.") from error
    return link


@router.delete("/exams/{exam_id}/specimen-types/{specimen_type_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_exam_specimen_type(
    exam_id: str,
    specimen_type_id: str,
    actor: User = Depends(catalog_writer),
    db: Session = Depends(get_db),
) -> Response:
    link = db.get(ExamSpecimenType, (exam_id, specimen_type_id))
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam-specimen relation not found.")
    before = snapshot(link)
    db.delete(link)
    record_audit(db, actor_user_id=actor.id, entity_type="exam_specimen_type", entity_id=exam_id, action="DELETE", before_data=before)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/exams/{exam_id}/parameters", response_model=list[ExamParameterResponse])
def list_exam_parameters(
    exam_id: str,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ExamParameter]:
    get_entity(db, Exam, exam_id, "Exam")
    return list(db.scalars(select(ExamParameter).where(ExamParameter.exam_id == exam_id).order_by(ExamParameter.display_order)))


@router.put("/exams/{exam_id}/parameters/{parameter_id}", response_model=ExamParameterResponse)
def set_exam_parameter(
    exam_id: str,
    parameter_id: str,
    payload: ExamParameterInput,
    actor: User = Depends(catalog_writer),
    db: Session = Depends(get_db),
) -> ExamParameter:
    get_active_entity(db, Exam, exam_id, "Exam")
    get_active_entity(db, ParameterDefinition, parameter_id, "Parameter")
    duplicate_order = db.scalar(
        select(ExamParameter).where(
            ExamParameter.exam_id == exam_id,
            ExamParameter.display_order == payload.display_order,
            ExamParameter.parameter_definition_id != parameter_id,
        )
    )
    if duplicate_order:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="display_order is already used by another exam parameter.")
    link = db.get(ExamParameter, (exam_id, parameter_id))
    before = snapshot(link) if link else None
    if link:
        link.display_order = payload.display_order
        link.external_code = payload.external_code
        link.is_required = payload.is_required
        action = "UPDATE"
    else:
        link = ExamParameter(
            exam_id=exam_id,
            parameter_definition_id=parameter_id,
            display_order=payload.display_order,
            external_code=payload.external_code,
            is_required=payload.is_required,
        )
        db.add(link)
        action = "CREATE"
    try:
        db.flush()
        record_audit(
            db,
            actor_user_id=actor.id,
            entity_type="exam_parameter",
            entity_id=exam_id,
            action=action,
            before_data=before,
            after_data=snapshot(link),
        )
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Exam-parameter relation conflicts with an existing record.") from error
    return link


@router.delete("/exams/{exam_id}/parameters/{parameter_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_exam_parameter(
    exam_id: str,
    parameter_id: str,
    actor: User = Depends(catalog_writer),
    db: Session = Depends(get_db),
) -> Response:
    link = db.get(ExamParameter, (exam_id, parameter_id))
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam-parameter relation not found.")
    before = snapshot(link)
    db.delete(link)
    record_audit(db, actor_user_id=actor.id, entity_type="exam_parameter", entity_id=exam_id, action="DELETE", before_data=before)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
