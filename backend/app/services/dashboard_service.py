from sqlalchemy.orm import Session

from app.repositories.dashboard_repository import DashboardRepository
from app.schemas.dashboard import DashboardAnalysisItem, DashboardResponse


class DashboardService:
    def __init__(self) -> None:
        self.repository = DashboardRepository()

    def get_dashboard(self, db: Session) -> DashboardResponse:
        rows = self.repository.get_dashboard(db)
        return DashboardResponse(
            analyses=[DashboardAnalysisItem(**row) for row in rows]
        )