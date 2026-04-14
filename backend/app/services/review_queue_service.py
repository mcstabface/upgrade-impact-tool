from sqlalchemy.orm import Session

from app.repositories.review_queue_repository import ReviewQueueRepository
from app.schemas.review_queue import ReviewQueueItem, ReviewQueueResponse


class ReviewQueueService:
    def __init__(self) -> None:
        self.repository = ReviewQueueRepository()

    def get_review_queue(self, db: Session) -> ReviewQueueResponse:
        rows = self.repository.get_open_review_items(db)
        return ReviewQueueResponse(items=[ReviewQueueItem(**row) for row in rows])