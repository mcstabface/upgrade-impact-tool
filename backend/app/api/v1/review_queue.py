from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.review_queue import ReviewQueueResponse
from app.services.review_queue_service import ReviewQueueService

router = APIRouter(tags=["review-queue"])
service = ReviewQueueService()


@router.get("/review-queue", response_model=ReviewQueueResponse)
def get_review_queue(db: Session = Depends(get_db)) -> ReviewQueueResponse:
    return service.get_review_queue(db)