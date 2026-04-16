from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import AuthenticatedUser, UserRole, require_roles
from app.db.session import get_db
from app.schemas.review_items import (
    ReviewItemCreateRequest,
    ReviewItemCreateResponse,
    ReviewItemDetailResponse,
    ReviewItemUpdateRequest,
    ReviewItemUpdateResponse,
)
from app.services.review_item_service import ReviewItemService
from app.services.usage_event_service import UsageEventService

router = APIRouter(tags=["review-items"])
service = ReviewItemService()
usage_event_service = UsageEventService()


@router.post("/review-items", response_model=ReviewItemCreateResponse)
def create_review_item(
    payload: ReviewItemCreateRequest,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.REVIEWER, UserRole.ADMIN)
    ),
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

    usage_event_service.record_event(
        db=db,
        event_type="REVIEW_ITEM_CREATED",
        actor_role=current_user.role.value,
        actor_user_id=current_user.user_id,
        entity_type="REVIEW_ITEM",
        entity_id=str(result.review_item_id),
        related_analysis_id=None,
        event_payload={
            "finding_id": payload.finding_id,
            "review_status": result.review_status,
            "assigned_owner_user_id": result.assigned_owner_user_id,
            "due_date": str(result.due_date),
        },
    )

    return result


@router.get("/review-items/{review_item_id}", response_model=ReviewItemDetailResponse)
def get_review_item(
    review_item_id: int,
    db: Session = Depends(get_db),
    _: AuthenticatedUser = Depends(
        require_roles(
            UserRole.VIEWER,
            UserRole.ANALYST,
            UserRole.REVIEWER,
            UserRole.ADMIN,
        )
    ),
) -> ReviewItemDetailResponse:
    result = service.get_review_item(db, review_item_id)
    if not result:
        raise HTTPException(status_code=404, detail="Review item not found")
    return result


@router.patch("/review-items/{review_item_id}", response_model=ReviewItemUpdateResponse)
def update_review_item(
    review_item_id: int,
    payload: ReviewItemUpdateRequest,
    db: Session = Depends(get_db),
    _: AuthenticatedUser = Depends(require_roles(UserRole.REVIEWER, UserRole.ADMIN)),
) -> ReviewItemUpdateResponse:
    try:
        result = service.update_review_item(db, review_item_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Review item update failed: {exc}",
        ) from exc

    if not result:
        raise HTTPException(status_code=404, detail="Review item not found")

    return result