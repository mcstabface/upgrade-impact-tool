from sqlalchemy import text
from sqlalchemy.orm import Session


class ReviewItemRepository:
    def get_finding_context(self, db: Session, finding_id: int) -> dict | None:
        query = text("""
            SELECT
                af.finding_id,
                af.analysis_id,
                af.headline,
                cr.application_name,
                fe.kb_article_number
            FROM analysis_findings af
            JOIN change_records cr ON cr.change_id = af.change_id
            JOIN finding_evidence fe ON fe.finding_id = af.finding_id
            WHERE af.finding_id = :finding_id
        """)
        row = db.execute(query, {"finding_id": finding_id}).first()
        return dict(row._mapping) if row else None

    def create_review_item(
        self,
        db: Session,
        *,
        finding_id: int,
        analysis_id: str,
        application_name: str,
        finding_headline: str,
        kb_reference: str,
        review_reason: str,
        assigned_owner_user_id: str,
        due_date: str,
        created_utc: int,
        created_by_user_id: str,
    ) -> dict:
        query = text("""
            INSERT INTO review_items (
                finding_id,
                analysis_id,
                application_name,
                finding_headline,
                kb_reference,
                review_reason,
                assigned_owner_user_id,
                due_date,
                review_status,
                created_utc,
                updated_utc,
                created_by_user_id
            ) VALUES (
                :finding_id,
                :analysis_id,
                :application_name,
                :finding_headline,
                :kb_reference,
                :review_reason,
                :assigned_owner_user_id,
                CAST(:due_date AS date),
                'OPEN',
                :created_utc,
                :created_utc,
                :created_by_user_id
            )
            RETURNING
                review_item_id,
                finding_id,
                review_status,
                assigned_owner_user_id,
                due_date::text AS due_date,
                created_utc
        """)
        row = db.execute(
            query,
            {
                "finding_id": finding_id,
                "analysis_id": analysis_id,
                "application_name": application_name,
                "finding_headline": finding_headline,
                "kb_reference": kb_reference,
                "review_reason": review_reason,
                "assigned_owner_user_id": assigned_owner_user_id,
                "due_date": due_date,
                "created_utc": created_utc,
                "created_by_user_id": created_by_user_id,
            },
        ).first()
        return dict(row._mapping)

    def get_review_item(self, db: Session, review_item_id: int) -> dict | None:
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
                created_by_user_id,
                resolution_note,
                defer_reason
            FROM review_items
            WHERE review_item_id = :review_item_id
        """)
        row = db.execute(query, {"review_item_id": review_item_id}).first()
        return dict(row._mapping) if row else None

    def get_review_item_status(self, db: Session, review_item_id: int) -> dict | None:
        query = text("""
            SELECT
                review_item_id,
                review_status,
                resolution_note,
                defer_reason
            FROM review_items
            WHERE review_item_id = :review_item_id
        """)
        row = db.execute(query, {"review_item_id": review_item_id}).first()
        return dict(row._mapping) if row else None

    def update_review_item_status(
        self,
        db: Session,
        *,
        review_item_id: int,
        review_status: str,
        updated_utc: int,
        resolution_note: str | None,
        defer_reason: str | None,
    ) -> dict:
        query = text("""
            UPDATE review_items
            SET
                review_status = :review_status,
                updated_utc = :updated_utc,
                resolution_note = :resolution_note,
                defer_reason = :defer_reason
            WHERE review_item_id = :review_item_id
            RETURNING
                review_item_id,
                review_status,
                updated_utc,
                resolution_note,
                defer_reason
        """)
        row = db.execute(
            query,
            {
                "review_item_id": review_item_id,
                "review_status": review_status,
                "updated_utc": updated_utc,
                "resolution_note": resolution_note,
                "defer_reason": defer_reason,
            },
        ).first()
        return dict(row._mapping)