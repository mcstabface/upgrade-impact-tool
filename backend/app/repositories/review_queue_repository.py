from sqlalchemy import text
from sqlalchemy.orm import Session


class ReviewQueueRepository:
    def get_open_review_items(self, db: Session) -> list[dict]:
        query = text("""
            SELECT
                review_item_id,
                finding_id,
                analysis_id,
                application_name,
                finding_headline,
                kb_reference,
                review_reason,
                assigned_owner_user_id,
                due_date::text AS due_date,
                review_status,
                created_utc,
                updated_utc,
                resolution_note,
                defer_reason,
                CASE
                    WHEN review_status IN ('OPEN', 'IN_PROGRESS', 'DEFERRED')
                     AND due_date < CURRENT_DATE
                    THEN true
                    ELSE false
                END AS is_overdue
            FROM review_items
            WHERE review_status IN ('OPEN', 'IN_PROGRESS', 'DEFERRED')
            ORDER BY
                CASE
                    WHEN due_date < CURRENT_DATE THEN 0
                    ELSE 1
                END,
                CASE review_status
                    WHEN 'OPEN' THEN 1
                    WHEN 'IN_PROGRESS' THEN 2
                    WHEN 'DEFERRED' THEN 3
                    ELSE 99
                END,
                due_date ASC,
                review_item_id DESC
        """)
        return [dict(row._mapping) for row in db.execute(query).all()]