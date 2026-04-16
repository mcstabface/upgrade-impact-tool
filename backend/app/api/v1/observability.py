from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import AuthenticatedUser, UserRole, require_roles
from app.db.session import get_db
from app.schemas.observability import ObservabilitySummaryResponse
from app.services.observability_service import ObservabilityService

router = APIRouter(tags=["observability"])
service = ObservabilityService()


@router.get("/observability/summary", response_model=ObservabilitySummaryResponse)
def get_observability_summary(
    db: Session = Depends(get_db),
    _: AuthenticatedUser = Depends(require_roles(UserRole.ADMIN)),
) -> ObservabilitySummaryResponse:
    return service.get_summary(db)