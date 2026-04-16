from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.notifications import NotificationSummaryResponse
from app.services.notification_service import NotificationService

router = APIRouter(tags=["notifications"])
service = NotificationService()


@router.get("/notifications", response_model=NotificationSummaryResponse)
def get_notifications(db: Session = Depends(get_db)) -> NotificationSummaryResponse:
    return service.get_notifications(db)