from pydantic import BaseModel


class ReviewQueueItem(BaseModel):
    finding_id: int
    analysis_id: str
    application_name: str
    finding_status: str
    severity: str
    headline: str
    reason_for_status: str | None


class ReviewQueueResponse(BaseModel):
    items: list[ReviewQueueItem]