from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.repositories.dashboard_repository import DashboardRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.review_queue_repository import ReviewQueueRepository
from app.schemas.notifications import (
    NotificationItem,
    NotificationReadResponse,
    NotificationSummaryResponse,
)


class NotificationService:
    def __init__(self) -> None:
        self.dashboard_repository = DashboardRepository()
        self.review_queue_repository = ReviewQueueRepository()
        self.notification_repository = NotificationRepository()

    def _utc_now(self) -> int:
        return int(datetime.now(UTC).timestamp())

    def _sync_notifications(self, db: Session) -> None:
        now_utc = self._utc_now()

        dashboard_analyses = self.dashboard_repository.get_dashboard(db)
        review_items = self.review_queue_repository.get_open_review_items(db)

        stale_notification_ids: list[str] = []
        overdue_notification_ids: list[str] = []

        stale_analyses = [
            analysis for analysis in dashboard_analyses if analysis.get("overall_status") == "STALE"
        ]
        for analysis in stale_analyses:
            notification_id = f"stale-{analysis['analysis_id']}"
            stale_notification_ids.append(notification_id)

            self.notification_repository.upsert_notification(
                db,
                {
                    "notification_id": notification_id,
                    "notification_type": "ANALYSIS_STALE",
                    "severity": "HIGH",
                    "headline": f"Analysis {analysis['analysis_id']} is stale",
                    "message": (
                        f"{analysis['customer_name']} — {analysis['environment_name']} "
                        "should be reviewed or refreshed before reuse."
                    ),
                    "target_path": f"/analyses/{analysis['analysis_id']}",
                    "now_utc": now_utc,
                },
            )

        overdue_review_items = [item for item in review_items if item.get("is_overdue")]
        for item in overdue_review_items:
            notification_id = f"overdue-review-{item['review_item_id']}"
            overdue_notification_ids.append(notification_id)

            self.notification_repository.upsert_notification(
                db,
                {
                    "notification_id": notification_id,
                    "notification_type": "REVIEW_ITEM_OVERDUE",
                    "severity": "HIGH",
                    "headline": f"Review item {item['review_item_id']} is overdue",
                    "message": (
                        f"{item['finding_headline']} is overdue for {item['assigned_owner_user_id']} "
                        f"and still in status {item['review_status']}."
                    ),
                    "target_path": f"/review-items/{item['review_item_id']}",
                    "now_utc": now_utc,
                },
            )

        self.notification_repository.deactivate_missing_notifications(
            db=db,
            notification_type="ANALYSIS_STALE",
            active_notification_ids=stale_notification_ids,
            now_utc=now_utc,
        )
        self.notification_repository.deactivate_missing_notifications(
            db=db,
            notification_type="REVIEW_ITEM_OVERDUE",
            active_notification_ids=overdue_notification_ids,
            now_utc=now_utc,
        )

    def get_notifications(self, db: Session) -> NotificationSummaryResponse:
        self._sync_notifications(db)
        db.commit()

        rows = self.notification_repository.get_active_notifications(db)
        unread_count = self.notification_repository.count_unread_active_notifications(db)

        return NotificationSummaryResponse(
            unread_count=unread_count,
            items=[NotificationItem(**row) for row in rows],
        )

    def mark_notification_read(self, db: Session, notification_id: str) -> NotificationReadResponse | None:
        result = self.notification_repository.mark_notification_read(
            db=db,
            notification_id=notification_id,
            now_utc=self._utc_now(),
        )
        if not result:
            return None

        db.commit()
        return NotificationReadResponse(**result)