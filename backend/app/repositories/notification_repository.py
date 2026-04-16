from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session


class NotificationRepository:
    def upsert_notification(self, db: Session, payload: dict) -> None:
        query = text(
            """
            INSERT INTO notification_deliveries (
                notification_id,
                notification_type,
                severity,
                headline,
                message,
                target_path,
                is_active,
                is_read,
                created_utc,
                updated_utc
            ) VALUES (
                :notification_id,
                :notification_type,
                :severity,
                :headline,
                :message,
                :target_path,
                true,
                false,
                :now_utc,
                :now_utc
            )
            ON CONFLICT (notification_id)
            DO UPDATE SET
                notification_type = EXCLUDED.notification_type,
                severity = EXCLUDED.severity,
                headline = EXCLUDED.headline,
                message = EXCLUDED.message,
                target_path = EXCLUDED.target_path,
                is_active = true,
                is_read = CASE
                    WHEN notification_deliveries.is_active = false THEN false
                    ELSE notification_deliveries.is_read
                END,
                updated_utc = EXCLUDED.updated_utc
            """
        )
        db.execute(
            query,
            {
                "notification_id": payload["notification_id"],
                "notification_type": payload["notification_type"],
                "severity": payload["severity"],
                "headline": payload["headline"],
                "message": payload["message"],
                "target_path": payload["target_path"],
                "now_utc": payload["now_utc"],
            },
        )

    def deactivate_missing_notifications(
        self,
        db: Session,
        notification_type: str,
        active_notification_ids: list[str],
        now_utc: int,
    ) -> None:
        if active_notification_ids:
            query = (
                text(
                    """
                    UPDATE notification_deliveries
                    SET
                        is_active = false,
                        updated_utc = :now_utc
                    WHERE notification_type = :notification_type
                      AND is_active = true
                      AND notification_id NOT IN :active_notification_ids
                    """
                ).bindparams(bindparam("active_notification_ids", expanding=True))
            )
            db.execute(
                query,
                {
                    "notification_type": notification_type,
                    "active_notification_ids": active_notification_ids,
                    "now_utc": now_utc,
                },
            )
            return

        query = text(
            """
            UPDATE notification_deliveries
            SET
                is_active = false,
                updated_utc = :now_utc
            WHERE notification_type = :notification_type
              AND is_active = true
            """
        )
        db.execute(
            query,
            {
                "notification_type": notification_type,
                "now_utc": now_utc,
            },
        )

    def get_active_notifications(self, db: Session) -> list[dict]:
        query = text(
            """
            SELECT
                notification_id,
                notification_type,
                severity,
                headline,
                message,
                target_path,
                is_read,
                created_utc,
                updated_utc
            FROM notification_deliveries
            WHERE is_active = true
            ORDER BY
                is_read ASC,
                CASE severity
                    WHEN 'HIGH' THEN 1
                    WHEN 'MEDIUM' THEN 2
                    WHEN 'LOW' THEN 3
                    ELSE 99
                END,
                updated_utc DESC,
                notification_id
            """
        )
        return [dict(row._mapping) for row in db.execute(query).all()]

    def count_unread_active_notifications(self, db: Session) -> int:
        query = text(
            """
            SELECT COUNT(*) AS unread_count
            FROM notification_deliveries
            WHERE is_active = true
              AND is_read = false
            """
        )
        row = db.execute(query).first()
        return row.unread_count or 0

    def mark_notification_read(self, db: Session, notification_id: str, now_utc: int) -> dict | None:
        query = text(
            """
            UPDATE notification_deliveries
            SET
                is_read = true,
                updated_utc = :now_utc
            WHERE notification_id = :notification_id
              AND is_active = true
            RETURNING
                notification_id,
                is_read,
                updated_utc
            """
        )
        row = db.execute(
            query,
            {
                "notification_id": notification_id,
                "now_utc": now_utc,
            },
        ).first()

        if not row:
            return None

        return dict(row._mapping)