from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.security import decode_access_token


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication is required.")
    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not active.")
    return user


def require_role(*allowed_roles: str) -> Callable:
    def dependency(user: User = Depends(get_current_user)) -> User:
        role_codes = {role.code for role in user.roles}
        if not role_codes.intersection(allowed_roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role permissions.")
        return user

    return dependency


def require_area_validation(area_id: str, final: bool, user: User) -> None:
    if {"ADMIN", "PROCESS_ADMIN"}.intersection(role.code for role in user.roles):
        return
    permission = next((item for item in user.area_permissions if item.laboratory_area_id == area_id), None)
    allowed = permission and (permission.can_final_validate if final else permission.can_preliminary_validate)
    if not allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Area validation permission is required.")
