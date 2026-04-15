from sqlalchemy.orm import Session

from app.repositories.dashboard_repository import DashboardRepository
from app.schemas.dashboard import DashboardResponse


class DashboardService:
    def __init__(self) -> None:
        self.repository = DashboardRepository()

    def get_dashboard(self, db: Session) -> DashboardResponse:
        analyses = self.repository.get_dashboard(db)
        top_risks = self.repository.get_top_risks(db)
        top_actions = self.repository.get_top_actions(db)
        review_item_summary = self.repository.get_review_item_summary(db)

        return DashboardResponse(
            analyses=analyses,
            top_risks=top_risks,
            top_actions=top_actions,
            review_item_summary=review_item_summary,
        )