from pydantic import BaseModel, Field


class ReviewCommentCreateRequest(BaseModel):
    comment_text: str = Field(min_length=1)
    created_by_user_id: str = Field(min_length=1)


class ReviewCommentResponse(BaseModel):
    comment_id: int
    review_item_id: int
    comment_text: str
    created_by_user_id: str
    created_utc: int


class ReviewCommentListResponse(BaseModel):
    items: list[ReviewCommentResponse]