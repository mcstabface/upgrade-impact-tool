from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import UserRole, require_roles
from app.db.session import get_db
from app.schemas.review_actions import ResolveFindingRequest, ResolveFindingResponse
from app.services.review_action_service import ReviewActionService

router = APIRouter(tags=["review-actions"])
service = ReviewActionService()


@router.post("/findings/{finding_id}/resolve", response_model=ResolveFindingResponse)
def resolve_finding(
    finding_id: int,
    payload: ResolveFindingRequest,
    db: Session = Depends(get_db),
    _: UserRole = Depends(require_roles(UserRole.REVIEWER, UserRole.ADMIN)),
) -> ResolveFindingResponse:
    result = service.resolve_finding(db, finding_id, payload.resolution_note)
    if not result:
        raise HTTPException(status_code=404, detail="Finding not found")

    db.commit()
    return ResolveFindingResponse(**result)