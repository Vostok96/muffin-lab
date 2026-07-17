from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.dependencies import require_role
from app.models import AuditEvent, LaboratoryArea, Role, User, UserAreaPermission, user_roles
from app.routers.auth import serialize_user
from app.schemas import AreaPermissionUpdate, AuditEventResponse, LaboratoryAreaCreate, RoleUpdate, UserCreate, UserResponse, UserUpdate
from app.security import hash_password
from app.services import get_roles, record_audit


router = APIRouter(prefix="/admin", tags=["Administration"])
require_admin = require_role("ADMIN")


def replace_area_permissions(db: Session, user: User, payload: AreaPermissionUpdate) -> None:
    area_ids = {permission.laboratory_area_id for permission in payload.area_permissions}
    areas = list(db.scalars(select(LaboratoryArea).where(LaboratoryArea.id.in_(area_ids)))) if area_ids else []
    if len(areas) != len(area_ids):
        raise ValueError("One or more laboratory areas do not exist.")
    user.area_permissions.clear()
    user.area_permissions.extend(
        UserAreaPermission(
            laboratory_area_id=permission.laboratory_area_id,
            can_preliminary_validate=permission.can_preliminary_validate,
            can_final_validate=permission.can_final_validate,
        )
        for permission in payload.area_permissions
    )


@router.get("/users", response_model=list[UserResponse])
def list_users(_: User = Depends(require_admin), db: Session = Depends(get_db)) -> list[UserResponse]:
    users = list(db.scalars(select(User).options(selectinload(User.roles)).order_by(User.username)))
    return [serialize_user(user) for user in users]


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, admin: User = Depends(require_admin), db: Session = Depends(get_db)) -> UserResponse:
    if db.scalar(select(User).where(User.username == payload.username)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists.")
    try:
        roles = get_roles(db, payload.role_codes)
        user = User(
            username=payload.username,
            given_name=payload.given_name,
            family_name=payload.family_name,
            password_hash=hash_password(payload.password),
            roles=roles,
        )
        replace_area_permissions(db, user, AreaPermissionUpdate(area_permissions=payload.area_permissions))
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error
    db.add(user)
    db.flush()
    record_audit(
        db,
        actor_user_id=admin.id,
        entity_type="user",
        entity_id=user.id,
        action="CREATE",
        after_data={"username": user.username, "roles": sorted(role.code for role in user.roles)},
    )
    db.commit()
    db.refresh(user)
    return serialize_user(user)


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: str, payload: UserUpdate, admin: User = Depends(require_admin), db: Session = Depends(get_db)) -> UserResponse:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    before = {"given_name": user.given_name, "family_name": user.family_name, "is_active": user.is_active}
    if payload.given_name is not None:
        user.given_name = payload.given_name
    if payload.family_name is not None:
        user.family_name = payload.family_name
    if payload.password is not None:
        user.password_hash = hash_password(payload.password)
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.role_codes is not None:
        try:
            user.roles = get_roles(db, payload.role_codes)
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error
    after = {"given_name": user.given_name, "family_name": user.family_name, "is_active": user.is_active}
    record_audit(db, actor_user_id=admin.id, entity_type="user", entity_id=user.id, action="UPDATE", before_data=before, after_data=after)
    db.commit()
    db.refresh(user)
    return serialize_user(user)


@router.put("/users/{user_id}/roles", response_model=UserResponse)
def update_user_roles(user_id: str, payload: RoleUpdate, admin: User = Depends(require_admin), db: Session = Depends(get_db)) -> UserResponse:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    before = sorted(role.code for role in user.roles)
    try:
        user.roles = get_roles(db, payload.role_codes)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error
    record_audit(db, actor_user_id=admin.id, entity_type="user", entity_id=user.id, action="ROLE_UPDATE", before_data={"roles": before}, after_data={"roles": sorted(role.code for role in user.roles)})
    db.commit()
    return serialize_user(user)


@router.put("/users/{user_id}/area-permissions", response_model=UserResponse)
def update_area_permissions(user_id: str, payload: AreaPermissionUpdate, admin: User = Depends(require_admin), db: Session = Depends(get_db)) -> UserResponse:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    try:
        replace_area_permissions(db, user, payload)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error
    record_audit(db, actor_user_id=admin.id, entity_type="user", entity_id=user.id, action="AREA_PERMISSION_UPDATE")
    db.commit()
    return serialize_user(user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_user(user_id: str, admin: User = Depends(require_admin), db: Session = Depends(get_db)) -> Response:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already inactive.")
    if any(role.code == "ADMIN" for role in user.roles):
        active_admins = db.scalar(
            select(func.count())
            .select_from(User)
            .join(user_roles, user_roles.c.user_id == User.id)
            .join(Role, Role.id == user_roles.c.role_id)
            .where(User.is_active.is_(True), Role.code == "ADMIN")
        ) or 0
        if active_admins <= 1:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="At least one active admin user is required.")
    user.is_active = False
    record_audit(db, actor_user_id=admin.id, entity_type="user", entity_id=user.id, action="DEACTIVATE", after_data={"username": user.username})
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/users/{user_id}/reactivate", response_model=UserResponse)
def reactivate_user(user_id: str, admin: User = Depends(require_admin), db: Session = Depends(get_db)) -> UserResponse:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    if user.is_active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already active.")
    user.is_active = True
    record_audit(db, actor_user_id=admin.id, entity_type="user", entity_id=user.id, action="REACTIVATE", after_data={"username": user.username})
    db.commit()
    return serialize_user(user)


@router.post("/areas", status_code=status.HTTP_201_CREATED)
def create_area(payload: LaboratoryAreaCreate, admin: User = Depends(require_admin), db: Session = Depends(get_db)) -> dict:
    code = payload.code.upper()
    if db.scalar(select(LaboratoryArea).where(LaboratoryArea.code == code)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Area code already exists.")
    area = LaboratoryArea(**(payload.model_dump() | {"code": code}))
    db.add(area)
    db.flush()
    record_audit(db, actor_user_id=admin.id, entity_type="laboratory_area", entity_id=area.id, action="CREATE", after_data={"code": area.code})
    db.commit()
    return {"id": area.id, "code": area.code, "name": area.name}


@router.get("/audit-events", response_model=list[AuditEventResponse])
def list_audit_events(_: User = Depends(require_admin), db: Session = Depends(get_db)) -> list[AuditEventResponse]:
    events = list(db.scalars(select(AuditEvent).order_by(AuditEvent.occurred_at.desc()).limit(100)))
    return [AuditEventResponse.model_validate(event, from_attributes=True) for event in events]
