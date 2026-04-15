from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import UserRole, require_roles
from app.db.session import get_db
from app.schemas.review_comments import (
    ReviewCommentCreateRequest,
    ReviewCommentListResponse,
    ReviewCommentResponse,
)
from app.services.review_comment_service import ReviewCommentService

router = APIRouter(tags=["review-comments"])
service = ReviewCommentService()


@router.post("/review-items/{review_item_id}/comments", response_model=ReviewCommentResponse)
def create_review_comment(
    review_item_id: int,
    payload: ReviewCommentCreateRequest,
    db: Session = Depends(get_db),
    _: UserRole = Depends(require_roles(UserRole.REVIEWER, UserRole.ADMIN)),
) -> ReviewCommentResponse:
    try:
        result = service.create_comment(db, review_item_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Review comment creation failed: {exc}",
        ) from exc

    if not result:
        raise HTTPException(status_code=404, detail="Review item not found")

    return result


@router.get("/review-items/{review_item_id}/comments", response_model=ReviewCommentListResponse)
def get_review_comments(
    review_item_id: int,
    db: Session = Depends(get_db),
) -> ReviewCommentListResponse:
    result = service.get_comments(db, review_item_id)
    if not result:
        raise HTTPException(status_code=404, detail="Review item not found")
    return result