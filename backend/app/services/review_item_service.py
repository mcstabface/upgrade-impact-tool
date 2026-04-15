import time
from datetime import date

from sqlalchemy.orm import Session

from app.repositories.review_item_repository import ReviewItemRepository
from app.schemas.review_items import (
    ReviewItemCreateRequest,
    ReviewItemCreateResponse,
    ReviewItemDetailResponse,
)


class ReviewItemService:
    def __init__(self) -> None:
        self.repository = ReviewItemRepository()

    def create_review_item(
        self,
        db: Session,
        payload: ReviewItemCreateRequest,
    ) -> ReviewItemCreateResponse | None:
        due_date = payload.due_date.strip()
        review_reason = payload.review_reason.strip()
        assigned_owner = payload.assigned_owner_user_id.strip()
        created_by = (payload.created_by_user_id or "system").strip()

        if not review_reason or not assigned_owner or not due_date:
            raise ValueError("review_reason, assigned_owner_user_id, and due_date are required")

        try:
            date.fromisoformat(due_date)
        except ValueError as exc:
            raise ValueError("due_date must be ISO format YYYY-MM-DD") from exc

        finding = self.repository.get_finding_context(db, payload.finding_id)
        if not finding:
            return None

        created = self.repository.create_review_item(
            db=db,
            finding_id=payload.finding_id,
            analysis_id=finding["analysis_id"],
            application_name=finding["application_name"],
            finding_headline=finding["headline"],
            kb_reference=finding["kb_article_number"],
            review_reason=review_reason,
            assigned_owner_user_id=assigned_owner,
            due_date=due_date,
            created_utc=int(time.time()),
            created_by_user_id=created_by,
        )

        db.commit()
        return ReviewItemCreateResponse(**created)

    def get_review_item(self, db: Session, review_item_id: int) -> ReviewItemDetailResponse | None:
        row = self.repository.get_review_item(db, review_item_id)
        if not row:
            return None
        return ReviewItemDetailResponse(**row)