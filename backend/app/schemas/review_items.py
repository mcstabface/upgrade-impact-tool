from pydantic import BaseModel, Field


class ReviewItemCreateRequest(BaseModel):
    finding_id: int
    review_reason: str = Field(min_length=1)
    assigned_owner_user_id: str = Field(min_length=1)
    due_date: str = Field(min_length=1)
    created_by_user_id: str | None = None


class ReviewItemCreateResponse(BaseModel):
    review_item_id: int
    finding_id: int
    review_status: str
    assigned_owner_user_id: str
    due_date: str
    created_utc: int


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