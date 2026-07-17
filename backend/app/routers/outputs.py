from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models import Clinician, LabOrder, Notification, OrderItem, PrintJob, User
from app.schemas import (
    CatalogPage,
    NotificationCreate,
    NotificationPatch,
    NotificationResponse,
    PrintJobCreate,
    PrintJobResponse,
)
from app.services import record_audit

router = APIRouter()
output_writer = require_role("ADMIN", "PROCESS_ADMIN", "ENTRY", "PROCESSOR")


def get_order_item(db: Session, order_item_id: str) -> OrderItem:
    item = db.get(OrderItem, order_item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order item not found.")
    return item


def commit_entity(db: Session, entity: Any, actor: User, entity_type: str, action: str) -> None:
    try:
        db.flush()
        record_audit(
            db,
            actor_user_id=actor.id,
            entity_type=entity_type,
            entity_id=entity.id,
            action=action,
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Record conflicts.")


# ---------------------------------------------------------------------------
# Print jobs
# ---------------------------------------------------------------------------


@router.get("/print-jobs", tags=["Outputs"], response_model=CatalogPage[PrintJobResponse])
def list_print_jobs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CatalogPage[PrintJobResponse]:
    total = db.scalar(select(func.count()).select_from(PrintJob)) or 0
    items = list(
        db.scalars(
            select(PrintJob)
            .order_by(PrintJob.requested_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    return CatalogPage(
        data=[PrintJobResponse.model_validate(item) for item in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.post("/print-jobs", tags=["Outputs"], response_model=PrintJobResponse, status_code=status.HTTP_201_CREATED)
def create_print_job(
    payload: PrintJobCreate,
    actor: User = Depends(output_writer),
    db: Session = Depends(get_db),
) -> PrintJob:
    get_order_item(db, payload.order_item_id)
    job = PrintJob(
        order_item_id=payload.order_item_id,
        kind=payload.kind,
        requested_by=actor.id,
        requested_at=datetime.now(timezone.utc),
        status="PENDING",
        details=payload.details,
    )
    db.add(job)
    record_audit(
        db,
        actor_user_id=actor.id,
        entity_type="print_job",
        entity_id=job.id,
        action="CREATE",
        after_data={"kind": job.kind, "order_item_id": job.order_item_id},
    )
    db.commit()
    db.refresh(job)
    return job


@router.patch("/print-jobs/{job_id}/complete", tags=["Outputs"], response_model=PrintJobResponse)
def complete_print_job(
    job_id: str,
    actor: User = Depends(output_writer),
    db: Session = Depends(get_db),
) -> PrintJob:
    job = db.get(PrintJob, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Print job not found.")
    if job.status != "PENDING":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Print job is not pending.")
    job.status = "PRINTED"
    job.printed_at = datetime.now(timezone.utc)
    record_audit(
        db,
        actor_user_id=actor.id,
        entity_type="print_job",
        entity_id=job.id,
        action="COMPLETE",
    )
    db.commit()
    db.refresh(job)
    return job


@router.patch("/print-jobs/{job_id}/fail", tags=["Outputs"], response_model=PrintJobResponse)
def fail_print_job(
    job_id: str,
    actor: User = Depends(output_writer),
    db: Session = Depends(get_db),
) -> PrintJob:
    job = db.get(PrintJob, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Print job not found.")
    if job.status != "PENDING":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Print job is not pending.")
    job.status = "FAILED"
    record_audit(
        db,
        actor_user_id=actor.id,
        entity_type="print_job",
        entity_id=job.id,
        action="FAIL",
    )
    db.commit()
    db.refresh(job)
    return job


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------


def resolve_recipient_for_item(db: Session, order_item_id: str) -> str:
    item = db.scalar(
        select(OrderItem)
        .where(OrderItem.id == order_item_id)
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order item not found.")
    order = db.scalar(
        select(LabOrder)
        .where(LabOrder.id == item.lab_order_id)
    )
    if order and order.clinician_id:
        clinician = db.get(Clinician, order.clinician_id)
        if clinician and clinician.email:
            return clinician.email
    return "clinician@example.invalid"


@router.get("/notifications", tags=["Outputs"], response_model=CatalogPage[NotificationResponse])
def list_notifications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CatalogPage[NotificationResponse]:
    total = db.scalar(select(func.count()).select_from(Notification)) or 0
    items = list(
        db.scalars(
            select(Notification)
            .order_by(Notification.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    return CatalogPage(
        data=[NotificationResponse.model_validate(item) for item in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.post("/notifications", tags=["Outputs"], response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
def create_notification(
    payload: NotificationCreate,
    actor: User = Depends(output_writer),
    db: Session = Depends(get_db),
) -> Notification:
    get_order_item(db, payload.order_item_id)
    notification = Notification(
        order_item_id=payload.order_item_id,
        type=payload.type,
        recipient=payload.recipient or resolve_recipient_for_item(db, payload.order_item_id),
        payload=payload.payload or {},
        status="PENDING",
    )
    db.add(notification)
    record_audit(
        db,
        actor_user_id=actor.id,
        entity_type="notification",
        entity_id=notification.id,
        action="CREATE",
        after_data={"type": notification.type, "recipient": notification.recipient},
    )
    db.commit()
    db.refresh(notification)
    return notification


@router.patch("/notifications/{notification_id}", tags=["Outputs"], response_model=NotificationResponse)
def update_notification(
    notification_id: str,
    payload: NotificationPatch,
    actor: User = Depends(output_writer),
    db: Session = Depends(get_db),
) -> Notification:
    notification = db.get(Notification, notification_id)
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    if payload.status is not None:
        notification.status = payload.status
        if payload.status == "SENT":
            notification.sent_at = datetime.now(timezone.utc)
    if payload.error_message is not None:
        notification.error_message = payload.error_message
    record_audit(
        db,
        actor_user_id=actor.id,
        entity_type="notification",
        entity_id=notification.id,
        action="UPDATE",
        after_data={"status": notification.status},
    )
    db.commit()
    db.refresh(notification)
    return notification


@router.post("/notifications/{notification_id}/retry", tags=["Outputs"], response_model=NotificationResponse)
def retry_notification(
    notification_id: str,
    actor: User = Depends(output_writer),
    db: Session = Depends(get_db),
) -> Notification:
    notification = db.get(Notification, notification_id)
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    if notification.status != "FAILED":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only failed notifications can be retried.")
    notification.status = "PENDING"
    notification.error_message = None
    notification.sent_at = None
    record_audit(
        db,
        actor_user_id=actor.id,
        entity_type="notification",
        entity_id=notification.id,
        action="RETRY",
    )
    db.commit()
    db.refresh(notification)
    return notification
