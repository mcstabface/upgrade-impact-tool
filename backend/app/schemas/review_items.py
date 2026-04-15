from pydantic import BaseModel, Field


class ReviewItemUpdateRequest(BaseModel):
    review_status: str | None = None
    assigned_owner_user_id: str | None = None
    due_date: str | None = None
    resolution_note: str | None = None
    defer_reason: str | None = None


class ReviewItemCreateResponse(BaseModel):
    review_item_id: int
    finding_id: int
    review_status: str
    assigned_owner_user_id: str
    due_date: str
    created_utc: int


class ReviewItemUpdateRequest(BaseModel):
    review_status: str = Field(min_length=1)
    resolution_note: str | None = None
    defer_reason: str | None = None


class ReviewItemUpdateResponse(BaseModel):
    review_item_id: int
    review_status: str
    assigned_owner_user_id: str
    due_date: str
    updated_utc: int
    assignment_updated_utc: int | None
    resolution_note: str | None
    defer_reason: str | None


class ReviewItemDetailResponse(BaseModel):
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
    created_by_user_id: str
    assignment_updated_utc: int | None
    resolution_note: str | None
    defer_reason: str | None