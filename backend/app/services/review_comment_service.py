import time

from sqlalchemy.orm import Session

from app.repositories.review_comment_repository import ReviewCommentRepository
from app.schemas.review_comments import (
    ReviewCommentCreateRequest,
    ReviewCommentListResponse,
    ReviewCommentResponse,
)


class ReviewCommentService:
    def __init__(self) -> None:
        self.repository = ReviewCommentRepository()

    def create_comment(
        self,
        db: Session,
        review_item_id: int,
        payload: ReviewCommentCreateRequest,
    ) -> ReviewCommentResponse | None:
        comment_text = payload.comment_text.strip()
        created_by_user_id = payload.created_by_user_id.strip()

        if not comment_text:
            raise ValueError("comment_text is required")

        if not created_by_user_id:
            raise ValueError("created_by_user_id is required")

        if not self.repository.review_item_exists(db, review_item_id):
            return None

        created = self.repository.create_comment(
            db=db,
            review_item_id=review_item_id,
            comment_text=comment_text,
            created_by_user_id=created_by_user_id,
            created_utc=int(time.time()),
        )
        db.commit()
        return ReviewCommentResponse(**created)

    def get_comments(self, db: Session, review_item_id: int) -> ReviewCommentListResponse | None:
        if not self.repository.review_item_exists(db, review_item_id):
            return None

        rows = self.repository.get_comments(db, review_item_id)
        return ReviewCommentListResponse(items=[ReviewCommentResponse(**row) for row in rows])