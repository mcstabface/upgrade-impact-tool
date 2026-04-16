import time

from sqlalchemy import text

from app.core.auth import hash_password
from app.db.session import SessionLocal

DEFAULT_USERS = [
    {
        "id": "user_admin_001",
        "email": "pilot.admin@example.com",
        "display_name": "Pilot Admin",
        "role": "ADMIN",
        "password": "ChangeMeNow!123",
    },
    {
        "id": "user_analyst_001",
        "email": "pilot.analyst@example.com",
        "display_name": "Pilot Analyst",
        "role": "ANALYST",
        "password": "ChangeMeNow!123",
    },
    {
        "id": "user_reviewer_001",
        "email": "pilot.reviewer@example.com",
        "display_name": "Pilot Reviewer",
        "role": "REVIEWER",
        "password": "ChangeMeNow!123",
    },
    {
        "id": "user_viewer_001",
        "email": "pilot.viewer@example.com",
        "display_name": "Pilot Viewer",
        "role": "VIEWER",
        "password": "ChangeMeNow!123",
    },
]


def main() -> None:
    now = int(time.time())

    with SessionLocal() as db:
        for user in DEFAULT_USERS:
            db.execute(
                text(
                    """
                    INSERT INTO users (
                        id,
                        email,
                        display_name,
                        password_hash,
                        is_active,
                        created_utc,
                        updated_utc
                    )
                    VALUES (
                        :id,
                        :email,
                        :display_name,
                        :password_hash,
                        TRUE,
                        :created_utc,
                        :updated_utc
                    )
                    ON CONFLICT (id) DO UPDATE
                    SET
                        email = EXCLUDED.email,
                        display_name = EXCLUDED.display_name,
                        password_hash = EXCLUDED.password_hash,
                        is_active = TRUE,
                        updated_utc = EXCLUDED.updated_utc
                    """
                ),
                {
                    "id": user["id"],
                    "email": user["email"],
                    "display_name": user["display_name"],
                    "password_hash": hash_password(user["password"]),
                    "created_utc": now,
                    "updated_utc": now,
                },
            )

            db.execute(
                text(
                    """
                    INSERT INTO user_roles (
                        user_id,
                        role,
                        created_utc,
                        updated_utc
                    )
                    VALUES (
                        :user_id,
                        :role,
                        :created_utc,
                        :updated_utc
                    )
                    ON CONFLICT (user_id) DO UPDATE
                    SET
                        role = EXCLUDED.role,
                        updated_utc = EXCLUDED.updated_utc
                    """
                ),
                {
                    "user_id": user["id"],
                    "role": user["role"],
                    "created_utc": now,
                    "updated_utc": now,
                },
            )

        db.commit()

    print("Pilot users seeded successfully.")


if __name__ == "__main__":
    main()