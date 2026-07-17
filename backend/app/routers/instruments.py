from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models import InstrumentMessage, OrderItem, User
from app.schemas import (
    CatalogPage,
    InstrumentMessageCreate,
    InstrumentMessagePatch,
    InstrumentMessageResponse,
)
from app.services import record_audit

router = APIRouter()
integration_writer = require_role("ADMIN", "PROCESS_ADMIN", "PROCESSOR")


@router.get("/instrument-messages", tags=["Instruments"], response_model=CatalogPage[InstrumentMessageResponse])
def list_instrument_messages(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CatalogPage[InstrumentMessageResponse]:
    total = db.scalar(select(func.count()).select_from(InstrumentMessage)) or 0
    items = list(
        db.scalars(
            select(InstrumentMessage)
            .order_by(InstrumentMessage.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    return CatalogPage(
        data=[InstrumentMessageResponse.model_validate(item) for item in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.post("/instrument-messages", tags=["Instruments"], response_model=InstrumentMessageResponse, status_code=status.HTTP_201_CREATED)
def create_instrument_message(
    payload: InstrumentMessageCreate,
    actor: User = Depends(integration_writer),
    db: Session = Depends(get_db),
) -> InstrumentMessage:
    if payload.order_item_id and not db.get(OrderItem, payload.order_item_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order item not found.")
    msg = InstrumentMessage(
        order_item_id=payload.order_item_id,
        direction=payload.direction,
        payload=payload.payload,
        status="PENDING",
        result_summary=payload.result_summary,
    )
    db.add(msg)
    record_audit(
        db,
        actor_user_id=actor.id,
        entity_type="instrument_message",
        entity_id=msg.id,
        action="CREATE",
        after_data={"direction": msg.direction, "status": msg.status},
    )
    db.commit()
    db.refresh(msg)
    return msg


@router.patch("/instrument-messages/{message_id}", tags=["Instruments"], response_model=InstrumentMessageResponse)
def update_instrument_message(
    message_id: str,
    payload: InstrumentMessagePatch,
    actor: User = Depends(integration_writer),
    db: Session = Depends(get_db),
) -> InstrumentMessage:
    msg = db.get(InstrumentMessage, message_id)
    if not msg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instrument message not found.")
    if payload.status is not None:
        msg.status = payload.status
        if payload.status in {"PROCESSED", "ACKNOWLEDGED", "FAILED"}:
            msg.processed_at = datetime.now(timezone.utc)
    if payload.result_summary is not None:
        msg.result_summary = payload.result_summary
    record_audit(
        db,
        actor_user_id=actor.id,
        entity_type="instrument_message",
        entity_id=msg.id,
        action="UPDATE",
        after_data={"status": msg.status},
    )
    db.commit()
    db.refresh(msg)
    return msg


@router.get("/order-items/{order_item_id}/instrument-messages", tags=["Instruments"], response_model=list[InstrumentMessageResponse])
def list_item_instrument_messages(
    order_item_id: str,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[InstrumentMessage]:
    if not db.get(OrderItem, order_item_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order item not found.")
    return list(
        db.scalars(
            select(InstrumentMessage)
            .where(InstrumentMessage.order_item_id == order_item_id)
            .order_by(InstrumentMessage.created_at.desc())
        )
    )
