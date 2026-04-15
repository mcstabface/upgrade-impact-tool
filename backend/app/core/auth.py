from enum import Enum

from fastapi import Depends, Header, HTTPException


class UserRole(str, Enum):
    VIEWER = "VIEWER"
    ANALYST = "ANALYST"
    REVIEWER = "REVIEWER"
    ADMIN = "ADMIN"


def get_current_role(
    x_user_role: str | None = Header(default=None, alias="X-User-Role"),
) -> UserRole:
    if x_user_role is None:
        return UserRole.VIEWER

    normalized_role = x_user_role.strip().upper()

    try:
        return UserRole(normalized_role)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role header: {x_user_role}",
        ) from exc


def require_roles(*allowed_roles: UserRole):
    def dependency(current_role: UserRole = Depends(get_current_role)) -> UserRole:
        if current_role not in allowed_roles:
            allowed = ", ".join(role.value for role in allowed_roles)
            raise HTTPException(
                status_code=403,
                detail=f"Role {current_role.value} is not permitted. Allowed roles: {allowed}",
            )
        return current_role

    return dependency