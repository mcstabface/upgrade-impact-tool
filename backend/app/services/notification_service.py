from sqlalchemy.orm import Session

from app.repositories.dashboard_repository import DashboardRepository
from app.repositories.review_queue_repository import ReviewQueueRepository
from app.schemas.notifications import NotificationItem, NotificationSummaryResponse


class NotificationService:
    def __init__(self) -> None:
        self.dashboard_repository = DashboardRepository()
        self.review_queue_repository = ReviewQueueRepository()

    def get_notifications(self, db: Session) -> NotificationSummaryResponse:
        dashboard_analyses = self.dashboard_repository.get_dashboard(db)
        review_items = self.review_queue_repository.get_open_review_items(db)

        items: list[NotificationItem] = []

        stale_analyses = [
            analysis for analysis in dashboard_analyses if analysis.get("overall_status") == "STALE"
        ]
        for analysis in stale_analyses:
            items.append(
                NotificationItem(
                    notification_id=f"stale-{analysis['analysis_id']}",
                    notification_type="ANALYSIS_STALE",
                    severity="HIGH",
                    headline=f"Analysis {analysis['analysis_id']} is stale",
                    message=(
                        f"{analysis['customer_name']} — {analysis['environment_name']} "
                        "should be reviewed or refreshed before reuse."
                    ),
                    target_path=f"/analyses/{analysis['analysis_id']}",
                )
            )

        overdue_review_items = [item for item in review_items if item.get("is_overdue")]
        for item in overdue_review_items:
            items.append(
                NotificationItem(
                    notification_id=f"overdue-review-{item['review_item_id']}",
                    notification_type="REVIEW_ITEM_OVERDUE",
                    severity="HIGH",
                    headline=f"Review item {item['review_item_id']} is overdue",
                    message=(
                        f"{item['finding_headline']} is overdue for {item['assigned_owner_user_id']} "
                        f"and still in status {item['review_status']}."
                    ),
                    target_path=f"/review-items/{item['review_item_id']}",
                )
            )

        items.sort(key=lambda item: (item.severity != "HIGH", item.notification_id))

        return NotificationSummaryResponse(
            unread_count=len(items),
            items=items,
        )