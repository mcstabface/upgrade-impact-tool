from sqlalchemy.orm import Session

from app.repositories.observability_repository import ObservabilityRepository
from app.schemas.observability import ObservabilityCountItem, ObservabilitySummaryResponse


class ObservabilityService:
    def __init__(self) -> None:
        self.repository = ObservabilityRepository()

    def get_summary(self, db: Session) -> ObservabilitySummaryResponse:
        counts = self.repository.get_system_counts(db)
        missing_inputs = self.repository.get_most_common_missing_inputs(db)
        review_reasons = self.repository.get_most_frequent_review_reasons(db)

        health_status = "ATTENTION_REQUIRED" if (
            counts["stale_analyses"] > 0 or counts["overdue_review_items"] > 0
        ) else "OK"

        return ObservabilitySummaryResponse(
            system_health_status=health_status,
            counts=[
                ObservabilityCountItem(label="Total Analyses", value=counts["total_analyses"]),
                ObservabilityCountItem(label="Stale Analyses", value=counts["stale_analyses"]),
                ObservabilityCountItem(label="Refreshed Analyses", value=counts["refreshed_analyses"]),
                ObservabilityCountItem(label="Active Review Items", value=counts["active_review_items"]),
                ObservabilityCountItem(label="Overdue Review Items", value=counts["overdue_review_items"]),
            ],
            most_common_missing_inputs=[
                ObservabilityCountItem(**row) for row in missing_inputs
            ],
            most_frequent_review_reasons=[
                ObservabilityCountItem(**row) for row in review_reasons
            ],
        )