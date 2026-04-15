from sqlalchemy import text
from sqlalchemy.orm import Session


class ReviewCommentRepository:
    def review_item_exists(self, db: Session, review_item_id: int) -> bool:
        query = text("""
            SELECT 1
            FROM review_items
            WHERE review_item_id = :review_item_id
        """)
        row = db.execute(query, {"review_item_id": review_item_id}).first()
        return row is not None

    def create_comment(
        self,
        db: Session,
        *,
        review_item_id: int,
        comment_text: str,
        created_by_user_id: str,
        created_utc: int,
    ) -> dict:
        query = text("""
            INSERT INTO review_comments (
                review_item_id,
                comment_text,
                created_by_user_id,
                created_utc
            ) VALUES (
                :review_item_id,
                :comment_text,
                :created_by_user_id,
                :created_utc
            )
            RETURNING
                comment_id,
                review_item_id,
                comment_text,
                created_by_user_id,
                created_utc
        """)
        row = db.execute(
            query,
            {
                "review_item_id": review_item_id,
                "comment_text": comment_text,
                "created_by_user_id": created_by_user_id,
                "created_utc": created_utc,
            },
        ).first()
        return dict(row._mapping)

    def get_comments(self, db: Session, review_item_id: int) -> list[dict]:
        query = text("""
            SELECT
                comment_id,
                review_item_id,
                comment_text,
                created_by_user_id,
                created_utc
            FROM review_comments
            WHERE review_item_id = :review_item_id
            ORDER BY created_utc ASC, comment_id ASC
        """)
        return [dict(row._mapping) for row in db.execute(query, {"review_item_id": review_item_id}).all()]