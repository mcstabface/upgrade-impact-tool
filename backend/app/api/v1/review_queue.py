from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.db.session import get_db
from app.schemas.review_queue import ReviewQueueResponse
from app.services.review_queue_export_service import ReviewQueueExportService
from app.services.review_queue_service import ReviewQueueService

router = APIRouter(tags=["review-queue"])
service = ReviewQueueService()
export_service = ReviewQueueExportService()


@router.get("/review-queue", response_model=ReviewQueueResponse)
def get_review_queue(db: Session = Depends(get_db)) -> ReviewQueueResponse:
    return service.get_review_queue(db)


@router.get("/review-queue/export.csv")
def export_review_queue_csv(db: Session = Depends(get_db)) -> Response:
    try:
        csv_content = export_service.export_csv(db)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": 'attachment; filename="review_queue.csv"',
            },
        )
    except Exception as exc:
        raise AppError(
            status_code=500,
            error_class="EXPORT_ERROR",
            message="Review queue export failed.",
            recovery_guidance=(
                "Retry the export. If the problem continues, return to the review queue "
                "and confirm the current review items are still accessible."
            ),
            retryable=True,
        ) from exc