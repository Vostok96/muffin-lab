from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models import (
    Antibiotic,
    AntimicrobialResult,
    AstPanel,
    AstPanelAntibiotic,
    ColonyCountOption,
    DefinedComment,
    Isolate,
    OrderItem,
    Organism,
    Result,
    User,
)
from app.schemas import (
    AntibioticCreate,
    AntibioticResponse,
    AntibioticUpdate,
    AntimicrobialResultInput,
    AntimicrobialResultResponse,
    AntimicrobialResultUpdate,
    AstPanelAntibioticInput,
    AstPanelAntibioticResponse,
    AstPanelCreate,
    AstPanelResponse,
    AstPanelUpdate,
    CatalogPage,
    CatalogResponse,
    ColonyCountOptionCreate,
    ColonyCountOptionResponse,
    ColonyCountOptionUpdate,
    DefinedCommentCreate,
    DefinedCommentResponse,
    DefinedCommentUpdate,
    IsolateCreate,
    IsolateResponse,
    IsolateUpdate,
    OrganismCreate,
    OrganismResponse,
    OrganismUpdate,
)
from app.services import autofill_antimicrobial_results, record_audit, record_workflow_event

router = APIRouter()
catalog_writer = require_role("ADMIN", "PROCESS_ADMIN")
isolate_editor = require_role("ADMIN", "PROCESS_ADMIN", "PROCESSOR")


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


def list_catalog_page(
    db: Session,
    model: type,
    response_model: type,
    active_only: bool,
    search: str | None,
    page: int,
    page_size: int,
) -> CatalogPage:
    filters = []
    if active_only:
        filters.append(model.is_active.is_(True))
    if search:
        term = f"%{search.strip()}%"
        filters.append(or_(model.code.ilike(term), model.name.ilike(term)))
    total = db.scalar(select(func.count()).select_from(model).where(*filters)) or 0
    order_column = model.name if model is Organism else getattr(model, "display_order", model.code)
    items = list(
        db.scalars(
            select(model)
            .where(*filters)
            .order_by(order_column, model.code)
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


def create_catalog(db: Session, model: type, payload: Any, actor: User, entity_type: str) -> Any:
    data = payload.model_dump()
    data["code"] = data["code"].upper()
    if db.scalar(select(model).where(model.code == data["code"])):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Catalog code already exists.")
    entity = model(**data)
    db.add(entity)
    try:
        db.flush()
        record_audit(
            db,
            actor_user_id=actor.id,
            entity_type=entity_type,
            entity_id=entity.id,
            action="CREATE",
            after_data={"code": entity.code, "name": entity.name},
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Catalog code conflicts with an existing record.")
    db.refresh(entity)
    return entity


def update_catalog(db: Session, entity: Any, payload: Any, actor: User, entity_type: str) -> Any:
    data = payload.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="At least one field must be provided.")
    if "code" in data:
        data["code"] = data["code"].upper()
        duplicate = db.scalar(
            select(entity.__class__).where(entity.__class__.code == data["code"], entity.__class__.id != entity.id)
        )
        if duplicate:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Catalog code already exists.")
    before = {"code": entity.code, "name": entity.name}
    for key, value in data.items():
        setattr(entity, key, value)
    try:
        db.flush()
        record_audit(
            db,
            actor_user_id=actor.id,
            entity_type=entity_type,
            entity_id=entity.id,
            action="UPDATE",
            before_data=before,
            after_data={"code": entity.code, "name": entity.name},
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Catalog values conflict with an existing record.")
    db.refresh(entity)
    return entity


# ---------------------------------------------------------------------------
# Organism catalog
# ---------------------------------------------------------------------------


@router.get("/catalogs/organisms", tags=["Catalogs"], response_model=CatalogPage[OrganismResponse])
def list_organisms(
    active_only: bool = True,
    search: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=3000),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CatalogPage[OrganismResponse]:
    return list_catalog_page(db, Organism, OrganismResponse, active_only, search, page, page_size)


@router.post("/catalogs/organisms", tags=["Catalogs"], response_model=OrganismResponse, status_code=status.HTTP_201_CREATED)
def create_organism(payload: OrganismCreate, actor: User = Depends(catalog_writer), db: Session = Depends(get_db)) -> Organism:
    return create_catalog(db, Organism, payload, actor, "organism")


@router.patch("/catalogs/organisms/{organism_id}", tags=["Catalogs"], response_model=OrganismResponse)
def update_organism(organism_id: str, payload: OrganismUpdate, actor: User = Depends(catalog_writer), db: Session = Depends(get_db)) -> Organism:
    return update_catalog(db, get_entity(db, Organism, organism_id, "Organism"), payload, actor, "organism")


# ---------------------------------------------------------------------------
# Colony count option catalog
# ---------------------------------------------------------------------------


@router.get("/catalogs/colony-count-options", tags=["Catalogs"], response_model=CatalogPage[ColonyCountOptionResponse])
def list_colony_count_options(
    active_only: bool = True,
    search: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CatalogPage[ColonyCountOptionResponse]:
    return list_catalog_page(db, ColonyCountOption, ColonyCountOptionResponse, active_only, search, page, page_size)


@router.post("/catalogs/colony-count-options", tags=["Catalogs"], response_model=ColonyCountOptionResponse, status_code=status.HTTP_201_CREATED)
def create_colony_count_option(payload: ColonyCountOptionCreate, actor: User = Depends(catalog_writer), db: Session = Depends(get_db)) -> ColonyCountOption:
    return create_catalog(db, ColonyCountOption, payload, actor, "colony_count_option")


@router.patch("/catalogs/colony-count-options/{option_id}", tags=["Catalogs"], response_model=ColonyCountOptionResponse)
def update_colony_count_option(
    option_id: str, payload: ColonyCountOptionUpdate, actor: User = Depends(catalog_writer), db: Session = Depends(get_db),
) -> ColonyCountOption:
    return update_catalog(db, get_entity(db, ColonyCountOption, option_id, "Colony count option"), payload, actor, "colony_count_option")


# ---------------------------------------------------------------------------
# Defined comment catalog
# ---------------------------------------------------------------------------


@router.get("/catalogs/defined-comments", tags=["Catalogs"], response_model=CatalogPage[DefinedCommentResponse])
def list_defined_comments(
    active_only: bool = True,
    search: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CatalogPage[DefinedCommentResponse]:
    return list_catalog_page(db, DefinedComment, DefinedCommentResponse, active_only, search, page, page_size)


@router.post("/catalogs/defined-comments", tags=["Catalogs"], response_model=DefinedCommentResponse, status_code=status.HTTP_201_CREATED)
def create_defined_comment(payload: DefinedCommentCreate, actor: User = Depends(catalog_writer), db: Session = Depends(get_db)) -> DefinedComment:
    return create_catalog(db, DefinedComment, payload, actor, "defined_comment")


@router.patch("/catalogs/defined-comments/{comment_id}", tags=["Catalogs"], response_model=DefinedCommentResponse)
def update_defined_comment(
    comment_id: str, payload: DefinedCommentUpdate, actor: User = Depends(catalog_writer), db: Session = Depends(get_db),
) -> DefinedComment:
    return update_catalog(db, get_entity(db, DefinedComment, comment_id, "Defined comment"), payload, actor, "defined_comment")


# ---------------------------------------------------------------------------
# Antibiotic catalog
# ---------------------------------------------------------------------------


@router.get("/catalogs/antibiotics", tags=["Catalogs"], response_model=CatalogPage[AntibioticResponse])
def list_antibiotics(
    active_only: bool = True,
    search: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CatalogPage[AntibioticResponse]:
    return list_catalog_page(db, Antibiotic, AntibioticResponse, active_only, search, page, page_size)


@router.post("/catalogs/antibiotics", tags=["Catalogs"], response_model=AntibioticResponse, status_code=status.HTTP_201_CREATED)
def create_antibiotic(payload: AntibioticCreate, actor: User = Depends(catalog_writer), db: Session = Depends(get_db)) -> Antibiotic:
    return create_catalog(db, Antibiotic, payload, actor, "antibiotic")


@router.patch("/catalogs/antibiotics/{antibiotic_id}", tags=["Catalogs"], response_model=AntibioticResponse)
def update_antibiotic(antibiotic_id: str, payload: AntibioticUpdate, actor: User = Depends(catalog_writer), db: Session = Depends(get_db)) -> Antibiotic:
    return update_catalog(db, get_entity(db, Antibiotic, antibiotic_id, "Antibiotic"), payload, actor, "antibiotic")


# ---------------------------------------------------------------------------
# AST panel catalog
# ---------------------------------------------------------------------------


@router.get("/catalogs/ast-panels", tags=["Catalogs"], response_model=CatalogPage[AstPanelResponse])
def list_ast_panels(
    active_only: bool = True,
    search: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CatalogPage[AstPanelResponse]:
    return list_catalog_page(db, AstPanel, AstPanelResponse, active_only, search, page, page_size)


@router.post("/catalogs/ast-panels", tags=["Catalogs"], response_model=AstPanelResponse, status_code=status.HTTP_201_CREATED)
def create_ast_panel(payload: AstPanelCreate, actor: User = Depends(catalog_writer), db: Session = Depends(get_db)) -> AstPanel:
    return create_catalog(db, AstPanel, payload, actor, "ast_panel")


@router.patch("/catalogs/ast-panels/{panel_id}", tags=["Catalogs"], response_model=AstPanelResponse)
def update_ast_panel(panel_id: str, payload: AstPanelUpdate, actor: User = Depends(catalog_writer), db: Session = Depends(get_db)) -> AstPanel:
    return update_catalog(db, get_entity(db, AstPanel, panel_id, "AST panel"), payload, actor, "ast_panel")


@router.get("/catalogs/ast-panels/{panel_id}/antibiotics", tags=["Catalogs"], response_model=list[AstPanelAntibioticResponse])
def list_ast_panel_antibiotics(
    panel_id: str,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AstPanelAntibiotic]:
    get_entity(db, AstPanel, panel_id, "AST panel")
    return list(
        db.scalars(
            select(AstPanelAntibiotic)
            .where(AstPanelAntibiotic.ast_panel_id == panel_id)
            .order_by(AstPanelAntibiotic.display_order)
        )
    )


@router.put("/catalogs/ast-panels/{panel_id}/antibiotics/{antibiotic_id}", tags=["Catalogs"], response_model=AstPanelAntibioticResponse)
def set_ast_panel_antibiotic(
    panel_id: str,
    antibiotic_id: str,
    payload: AstPanelAntibioticInput,
    actor: User = Depends(catalog_writer),
    db: Session = Depends(get_db),
) -> AstPanelAntibiotic:
    get_active_entity(db, AstPanel, panel_id, "AST panel")
    get_active_entity(db, Antibiotic, antibiotic_id, "Antibiotic")
    link = db.get(AstPanelAntibiotic, (panel_id, antibiotic_id))
    action = "CREATE" if not link else "UPDATE"
    if link:
        link.display_order = payload.display_order
        link.default_method = payload.default_method
        link.default_interpretation = payload.default_interpretation
    else:
        link = AstPanelAntibiotic(
            ast_panel_id=panel_id,
            antibiotic_id=antibiotic_id,
            display_order=payload.display_order,
            default_method=payload.default_method,
            default_interpretation=payload.default_interpretation,
        )
        db.add(link)
    try:
        db.flush()
        record_audit(
            db,
            actor_user_id=actor.id,
            entity_type="ast_panel_antibiotic",
            entity_id=panel_id,
            action=action,
            after_data={
                "antibiotic_id": antibiotic_id,
                "display_order": payload.display_order,
                "default_method": payload.default_method,
                "default_interpretation": payload.default_interpretation,
            },
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Panel-antibiotic relation conflicts.")
    return link


@router.delete("/catalogs/ast-panels/{panel_id}/antibiotics/{antibiotic_id}", tags=["Catalogs"], status_code=status.HTTP_204_NO_CONTENT)
def remove_ast_panel_antibiotic(
    panel_id: str,
    antibiotic_id: str,
    actor: User = Depends(catalog_writer),
    db: Session = Depends(get_db),
) -> Response:
    link = db.get(AstPanelAntibiotic, (panel_id, antibiotic_id))
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Panel-antibiotic relation not found.")
    db.delete(link)
    record_audit(db, actor_user_id=actor.id, entity_type="ast_panel_antibiotic", entity_id=panel_id, action="DELETE", after_data={"antibiotic_id": antibiotic_id})
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Isolate management
# ---------------------------------------------------------------------------

isolate_response_404 = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Isolate not found.")


def get_isolate(db: Session, isolate_id: str, *, for_update: bool = False) -> Isolate:
    statement = select(Isolate).where(Isolate.id == isolate_id)
    if for_update:
        statement = statement.with_for_update()
    isolate = db.scalar(statement)
    if not isolate:
        raise isolate_response_404
    return isolate


def get_result(db: Session, result_id: str) -> Result:
    result = db.get(Result, result_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Result not found.")
    return result


def prepare_result_for_microbiology_edit(db: Session, result: Result, actor: User) -> None:
    if result.status == "FINAL_VALIDATED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Final validated results must be reopened before editing.",
        )
    now = datetime.now(timezone.utc)
    item = db.get(OrderItem, result.order_item_id)
    if result.status == "PRELIMINARY_VALIDATED":
        result.status = "RESULT_SAVED"
        result.preliminary_at = None
        result.preliminary_by = None
        if item:
            item.status = "RESULT_SAVED"
            record_workflow_event(
                db,
                order_item_id=item.id,
                event_type="PRELIMINARY_INVALIDATED",
                performed_by=actor.id,
                details={"reason": "Microbiology identification or AST was edited."},
            )
    result.saved_at = now
    result.saved_by = actor.id


def isolate_snapshot(isolate: Isolate) -> dict[str, Any]:
    return {
        "organism_id": isolate.organism_id,
        "colony_count_option_id": isolate.colony_count_option_id,
        "phenotype": isolate.phenotype,
        "comment": isolate.comment,
        "ast_panel_id": isolate.ast_panel_id,
    }


@router.get("/results/{result_id}/isolates", tags=["Microbiology"], response_model=list[IsolateResponse])
def list_isolates(
    result_id: str,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Isolate]:
    get_result(db, result_id)
    return list(
        db.scalars(
            select(Isolate)
            .where(Isolate.result_id == result_id)
            .order_by(Isolate.created_at)
        )
    )


@router.post("/results/{result_id}/isolates", tags=["Microbiology"], response_model=IsolateResponse, status_code=status.HTTP_201_CREATED)
def create_isolate(
    result_id: str,
    payload: IsolateCreate,
    actor: User = Depends(isolate_editor),
    db: Session = Depends(get_db),
) -> Isolate:
    result = get_result(db, result_id)
    prepare_result_for_microbiology_edit(db, result, actor)
    get_active_entity(db, Organism, payload.organism_id, "Organism")
    if payload.colony_count_option_id:
        get_active_entity(db, ColonyCountOption, payload.colony_count_option_id, "Colony count option")
    if payload.ast_panel_id:
        get_active_entity(db, AstPanel, payload.ast_panel_id, "AST panel")
    isolate = Isolate(
        result_id=result.id,
        **payload.model_dump(),
    )
    db.add(isolate)
    db.flush()
    if payload.ast_panel_id:
        autofill_antimicrobial_results(db, isolate_id=isolate.id, ast_panel_id=payload.ast_panel_id, default_method="DISCO")
        db.flush()
    record_audit(
        db,
        actor_user_id=actor.id,
        entity_type="isolate",
        entity_id=isolate.id,
        action="CREATE",
        after_data=isolate_snapshot(isolate),
    )
    db.commit()
    db.refresh(isolate)
    return isolate


@router.get("/results/{result_id}/isolates/{isolate_id}", tags=["Microbiology"], response_model=IsolateResponse)
def get_isolate_detail(
    result_id: str,
    isolate_id: str,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Isolate:
    get_result(db, result_id)
    isolate = get_isolate(db, isolate_id)
    if isolate.result_id != result_id:
        raise isolate_response_404
    return isolate


@router.patch("/results/{result_id}/isolates/{isolate_id}", tags=["Microbiology"], response_model=IsolateResponse)
def update_isolate(
    result_id: str,
    isolate_id: str,
    payload: IsolateUpdate,
    actor: User = Depends(isolate_editor),
    db: Session = Depends(get_db),
) -> Isolate:
    result = get_result(db, result_id)
    prepare_result_for_microbiology_edit(db, result, actor)
    isolate = get_isolate(db, isolate_id, for_update=True)
    if isolate.result_id != result_id:
        raise isolate_response_404
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="At least one field must be provided.")
    if "organism_id" in changes:
        get_active_entity(db, Organism, changes["organism_id"], "Organism")
    if changes.get("colony_count_option_id"):
        get_active_entity(db, ColonyCountOption, changes["colony_count_option_id"], "Colony count option")
    panel_changed = "ast_panel_id" in changes and changes["ast_panel_id"] != isolate.ast_panel_id
    new_panel_id = changes.get("ast_panel_id")
    if new_panel_id:
        get_active_entity(db, AstPanel, new_panel_id, "AST panel")
    before = isolate_snapshot(isolate)
    for key, value in changes.items():
        setattr(isolate, key, value)
    if panel_changed:
        allowed_antibiotics = set()
        if new_panel_id:
            allowed_antibiotics = set(
                db.scalars(
                    select(AstPanelAntibiotic.antibiotic_id).where(
                        AstPanelAntibiotic.ast_panel_id == new_panel_id
                    )
                )
            )
        for ast_row in db.scalars(
            select(AntimicrobialResult).where(AntimicrobialResult.isolate_id == isolate.id)
        ):
            if ast_row.antibiotic_id not in allowed_antibiotics:
                db.delete(ast_row)
        if new_panel_id:
            autofill_antimicrobial_results(db, isolate_id=isolate.id, ast_panel_id=new_panel_id, default_method="DISCO")
        db.flush()
    record_audit(
        db,
        actor_user_id=actor.id,
        entity_type="isolate",
        entity_id=isolate.id,
        action="UPDATE",
        before_data=before,
        after_data=isolate_snapshot(isolate),
    )
    db.commit()
    db.refresh(isolate)
    return isolate


@router.delete("/results/{result_id}/isolates/{isolate_id}", tags=["Microbiology"], status_code=status.HTTP_204_NO_CONTENT)
def delete_isolate(
    result_id: str,
    isolate_id: str,
    actor: User = Depends(catalog_writer),
    db: Session = Depends(get_db),
) -> Response:
    result = get_result(db, result_id)
    prepare_result_for_microbiology_edit(db, result, actor)
    isolate = get_isolate(db, isolate_id)
    if isolate.result_id != result_id:
        raise isolate_response_404
    snapshot = isolate_snapshot(isolate)
    for ast_row in db.scalars(
        select(AntimicrobialResult).where(AntimicrobialResult.isolate_id == isolate.id)
    ):
        db.delete(ast_row)
    db.flush()
    db.delete(isolate)
    record_audit(db, actor_user_id=actor.id, entity_type="isolate", entity_id=isolate_id, action="DELETE", before_data=snapshot)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Antimicrobial result management
# ---------------------------------------------------------------------------

ar_not_found = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Antimicrobial result not found.")


def get_antimicrobial_result(db: Session, ar_id: str, *, for_update: bool = False) -> AntimicrobialResult:
    statement = select(AntimicrobialResult).where(AntimicrobialResult.id == ar_id)
    if for_update:
        statement = statement.with_for_update()
    ar = db.scalar(statement)
    if not ar:
        raise ar_not_found
    return ar


def ar_snapshot(ar: AntimicrobialResult) -> dict[str, Any]:
    return {
        "antibiotic_id": ar.antibiotic_id,
        "mic_value": ar.mic_value,
        "interpretation": ar.interpretation,
        "method": ar.method,
        "is_reportable": ar.is_reportable,
    }


@router.get("/isolates/{isolate_id}/antimicrobial-results", tags=["Microbiology"], response_model=list[AntimicrobialResultResponse])
def list_antimicrobial_results(
    isolate_id: str,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AntimicrobialResult]:
    get_isolate(db, isolate_id)
    return list(
        db.scalars(
            select(AntimicrobialResult)
            .where(AntimicrobialResult.isolate_id == isolate_id)
            .order_by(AntimicrobialResult.id)
        )
    )


@router.post("/isolates/{isolate_id}/antimicrobial-results", tags=["Microbiology"], response_model=AntimicrobialResultResponse, status_code=status.HTTP_201_CREATED)
def create_antimicrobial_result(
    isolate_id: str,
    payload: AntimicrobialResultInput,
    actor: User = Depends(isolate_editor),
    db: Session = Depends(get_db),
) -> AntimicrobialResult:
    isolate = get_isolate(db, isolate_id)
    prepare_result_for_microbiology_edit(db, get_result(db, isolate.result_id), actor)
    get_active_entity(db, Antibiotic, payload.antibiotic_id, "Antibiotic")
    existing = db.scalar(
        select(AntimicrobialResult).where(
            AntimicrobialResult.isolate_id == isolate_id,
            AntimicrobialResult.antibiotic_id == payload.antibiotic_id,
        )
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Antimicrobial result already exists for this antibiotic.")
    ar = AntimicrobialResult(isolate_id=isolate.id, **payload.model_dump())
    db.add(ar)
    db.flush()
    record_audit(
        db,
        actor_user_id=actor.id,
        entity_type="antimicrobial_result",
        entity_id=ar.id,
        action="CREATE",
        after_data=ar_snapshot(ar),
    )
    db.commit()
    db.refresh(ar)
    return ar


@router.patch("/isolates/{isolate_id}/antimicrobial-results/{ar_id}", tags=["Microbiology"], response_model=AntimicrobialResultResponse)
def update_antimicrobial_result(
    isolate_id: str,
    ar_id: str,
    payload: AntimicrobialResultUpdate,
    actor: User = Depends(isolate_editor),
    db: Session = Depends(get_db),
) -> AntimicrobialResult:
    isolate = get_isolate(db, isolate_id)
    prepare_result_for_microbiology_edit(db, get_result(db, isolate.result_id), actor)
    ar = get_antimicrobial_result(db, ar_id, for_update=True)
    if ar.isolate_id != isolate_id:
        raise ar_not_found
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="At least one field must be provided.")
    before = ar_snapshot(ar)
    for key, value in changes.items():
        setattr(ar, key, value)
    record_audit(
        db,
        actor_user_id=actor.id,
        entity_type="antimicrobial_result",
        entity_id=ar.id,
        action="UPDATE",
        before_data=before,
        after_data=ar_snapshot(ar),
    )
    db.commit()
    db.refresh(ar)
    return ar
