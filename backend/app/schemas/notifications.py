from pydantic import BaseModel


class NotificationItem(BaseModel):
    notification_id: str
    notification_type: str
    severity: str
    headline: str
    message: str
    target_path: str
    is_read: bool


class NotificationSummaryResponse(BaseModel):
    unread_count: int
    items: list[NotificationItem]


class NotificationReadResponse(BaseModel):
    notification_id: str
    is_read: bool
    updated_utc: int