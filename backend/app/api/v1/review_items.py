from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.review_items import (
    ReviewItemCreateRequest,
    ReviewItemCreateResponse,
    ReviewItemDetailResponse,
)
from app.services.review_item_service import ReviewItemService

router = APIRouter(tags=["review-items"])
service = ReviewItemService()


@router.post("/review-items", response_model=ReviewItemCreateResponse)
def create_review_item(
    payload: ReviewItemCreateRequest,
    db: Session = Depends(get_db),
) -> ReviewItemCreateResponse:
    try:
        result = service.create_review_item(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Review item creation failed: {exc}",
        ) from exc

    if not result:
        raise HTTPException(status_code=404, detail="Finding not found")

    return result


@router.get("/review-items/{review_item_id}", response_model=ReviewItemDetailResponse)
def get_review_item(
    review_item_id: int,
    db: Session = Depends(get_db),
) -> ReviewItemDetailResponse:
    result = service.get_review_item(db, review_item_id)
    if not result:
        raise HTTPException(status_code=404, detail="Review item not found")
    return result