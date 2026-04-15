from pydantic import BaseModel


class ReviewQueueItem(BaseModel):
    review_item_id: int
    finding_id: int
    analysis_id: str
    application_name: str
    finding_headline: str
    kb_reference: str
    review_reason: str
    assigned_owner_user_id: str
    due_date: str
    review_status: str
    created_utc: int
    updated_utc: int
    resolution_note: str | None = None
    defer_reason: str | None = None
    is_overdue: bool


class ReviewQueueResponse(BaseModel):
    items: list[ReviewQueueItem]