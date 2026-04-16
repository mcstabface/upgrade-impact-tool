from collections import Counter

from sqlalchemy.orm import Session

from app.repositories.observability_repository import ObservabilityRepository
from app.schemas.observability import ObservabilityCountItem, ObservabilitySummaryResponse
from app.services.intake_validation_service import IntakeValidationService


class ObservabilityService:
    def __init__(self) -> None:
        self.repository = ObservabilityRepository()
        self.intake_validation_service = IntakeValidationService()

    def get_summary(self, db: Session) -> ObservabilitySummaryResponse:
        counts = self.repository.get_system_counts(db)
        blocked_payload_rows = self.repository.get_blocked_intake_payloads(db)
        missing_inputs = self.repository.get_most_common_missing_inputs(db)
        review_reasons = self.repository.get_most_frequent_review_reasons(db)

        blocked_field_counts: Counter[str] = Counter()
        for row in blocked_payload_rows:
            payload = row.get("payload_json") or {}
            validation_result = self.intake_validation_service.validate(payload)
            blocked_field_counts.update(validation_result.missing_required_fields)

        blocked_fields = [
            ObservabilityCountItem(label=label, value=value)
            for label, value in sorted(
                blocked_field_counts.items(),
                key=lambda item: (-item[1], item[0]),
            )[:5]
        ]

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
            most_common_blocked_fields=blocked_fields,
            most_common_missing_inputs=[
                ObservabilityCountItem(**row) for row in missing_inputs
            ],
            most_frequent_review_reasons=[
                ObservabilityCountItem(**row) for row in review_reasons
            ],
        )