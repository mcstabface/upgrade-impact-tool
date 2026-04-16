from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.notifications import NotificationReadResponse, NotificationSummaryResponse
from app.services.notification_service import NotificationService

router = APIRouter(tags=["notifications"])
service = NotificationService()


@router.get("/notifications", response_model=NotificationSummaryResponse)
def get_notifications(db: Session = Depends(get_db)) -> NotificationSummaryResponse:
    return service.get_notifications(db)


@router.patch("/notifications/{notification_id}/read", response_model=NotificationReadResponse)
def mark_notification_read(
    notification_id: str,
    db: Session = Depends(get_db),
) -> NotificationReadResponse:
    result = service.mark_notification_read(db, notification_id)
    if not result:
        raise HTTPException(status_code=404, detail="Notification not found")
    return result