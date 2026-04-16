from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.auth import (
    AuthenticatedUser,
    authenticate_user,
    create_session,
    get_current_user,
    revoke_session,
)
from app.core.config import settings
from app.db.session import get_db

router = APIRouter(tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthMeResponse(BaseModel):
    user_id: str
    email: str
    display_name: str
    role: str


@router.post("/auth/login", response_model=AuthMeResponse)
def login(
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthMeResponse:
    user = authenticate_user(
        db,
        email=payload.email,
        password=payload.password,
    )

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    session_token = create_session(db, user_id=user.user_id)
    db.commit()

    response.set_cookie(
        key=settings.auth_cookie_name,
        value=session_token,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="lax",
        max_age=settings.auth_session_ttl_seconds,
        path="/",
    )

    return AuthMeResponse(
        user_id=user.user_id,
        email=user.email,
        display_name=user.display_name,
        role=user.role.value,
    )


@router.post("/auth/logout", status_code=204)
def logout(
    response: Response,
    db: Session = Depends(get_db),
    session_token: str | None = Cookie(default=None, alias="uit_session"),
) -> Response:
    if session_token:
        revoke_session(db, session_token=session_token)
        db.commit()

    response.delete_cookie(
        key=settings.auth_cookie_name,
        path="/",
    )

    return response


@router.get("/auth/me", response_model=AuthMeResponse)
def get_me(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AuthMeResponse:
    return AuthMeResponse(
        user_id=current_user.user_id,
        email=current_user.email,
        display_name=current_user.display_name,
        role=current_user.role.value,
    )