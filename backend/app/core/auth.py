import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass
from enum import Enum

from fastapi import Cookie, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db


class UserRole(str, Enum):
    VIEWER = "VIEWER"
    ANALYST = "ANALYST"
    REVIEWER = "REVIEWER"
    ADMIN = "ADMIN"


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: str
    email: str
    display_name: str
    role: UserRole


def _hash_value(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password=password.encode("utf-8"),
        salt=salt,
        n=16384,
        r=8,
        p=1,
        dklen=64,
    )
    return f"scrypt${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, salt_hex, digest_hex = stored_hash.split("$", 2)
    except ValueError:
        return False

    if algorithm != "scrypt":
        return False

    derived = hashlib.scrypt(
        password=password.encode("utf-8"),
        salt=bytes.fromhex(salt_hex),
        n=16384,
        r=8,
        p=1,
        dklen=64,
    )

    return hmac.compare_digest(derived.hex(), digest_hex)


def authenticate_user(
    db: Session,
    *,
    email: str,
    password: str,
) -> AuthenticatedUser | None:
    row = (
        db.execute(
            text(
                """
                SELECT
                    u.id,
                    u.email,
                    u.display_name,
                    u.password_hash,
                    ur.role
                FROM users u
                JOIN user_roles ur
                    ON ur.user_id = u.id
                WHERE LOWER(u.email) = LOWER(:email)
                  AND u.is_active = TRUE
                LIMIT 1
                """
            ),
            {"email": email},
        )
        .mappings()
        .first()
    )

    if row is None:
        return None

    if not verify_password(password, row["password_hash"]):
        return None

    return AuthenticatedUser(
        user_id=row["id"],
        email=row["email"],
        display_name=row["display_name"],
        role=UserRole(row["role"]),
    )


def create_session(
    db: Session,
    *,
    user_id: str,
) -> str:
    raw_token = secrets.token_urlsafe(48)
    session_id = f"sess_{secrets.token_hex(12)}"
    now = int(time.time())
    expires_utc = now + settings.auth_session_ttl_seconds

    db.execute(
        text(
            """
            INSERT INTO user_sessions (
                id,
                user_id,
                session_token_hash,
                created_utc,
                expires_utc,
                revoked_utc,
                last_seen_utc
            )
            VALUES (
                :id,
                :user_id,
                :session_token_hash,
                :created_utc,
                :expires_utc,
                NULL,
                :last_seen_utc
            )
            """
        ),
        {
            "id": session_id,
            "user_id": user_id,
            "session_token_hash": _hash_value(raw_token),
            "created_utc": now,
            "expires_utc": expires_utc,
            "last_seen_utc": now,
        },
    )

    return raw_token


def revoke_session(
    db: Session,
    *,
    session_token: str,
) -> None:
    now = int(time.time())

    db.execute(
        text(
            """
            UPDATE user_sessions
            SET revoked_utc = :revoked_utc
            WHERE session_token_hash = :session_token_hash
              AND revoked_utc IS NULL
            """
        ),
        {
            "revoked_utc": now,
            "session_token_hash": _hash_value(session_token),
        },
    )


def get_current_user(
    db: Session = Depends(get_db),
    session_token: str | None = Cookie(default=None, alias=settings.auth_cookie_name),
) -> AuthenticatedUser:
    if session_token is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    now = int(time.time())

    row = (
        db.execute(
            text(
                """
                SELECT
                    u.id,
                    u.email,
                    u.display_name,
                    ur.role,
                    us.id AS session_id
                FROM user_sessions us
                JOIN users u
                    ON u.id = us.user_id
                JOIN user_roles ur
                    ON ur.user_id = u.id
                WHERE us.session_token_hash = :session_token_hash
                  AND us.revoked_utc IS NULL
                  AND us.expires_utc > :now
                  AND u.is_active = TRUE
                LIMIT 1
                """
            ),
            {
                "session_token_hash": _hash_value(session_token),
                "now": now,
            },
        )
        .mappings()
        .first()
    )

    if row is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    db.execute(
        text(
            """
            UPDATE user_sessions
            SET last_seen_utc = :last_seen_utc
            WHERE id = :session_id
            """
        ),
        {
            "last_seen_utc": now,
            "session_id": row["session_id"],
        },
    )

    return AuthenticatedUser(
        user_id=row["id"],
        email=row["email"],
        display_name=row["display_name"],
        role=UserRole(row["role"]),
    )


def require_roles(*allowed_roles: UserRole):
    def dependency(
        current_user: AuthenticatedUser = Depends(get_current_user),
    ) -> AuthenticatedUser:
        if current_user.role not in allowed_roles:
            allowed = ", ".join(role.value for role in allowed_roles)
            raise HTTPException(
                status_code=403,
                detail=(
                    f"Role {current_user.role.value} is not permitted. "
                    f"Allowed roles: {allowed}"
                ),
            )
        return current_user

    return dependency