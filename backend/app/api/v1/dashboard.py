from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import AuthenticatedUser, UserRole, require_roles
from app.db.session import get_db
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(tags=["dashboard"])
service = DashboardService()


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    db: Session = Depends(get_db),
    _: AuthenticatedUser = Depends(
        require_roles(
            UserRole.VIEWER,
            UserRole.ANALYST,
            UserRole.REVIEWER,
            UserRole.ADMIN,
        )
    ),
) -> DashboardResponse:
    return service.get_dashboard(db)