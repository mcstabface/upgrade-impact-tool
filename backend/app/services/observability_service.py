from collections import Counter

from sqlalchemy.orm import Session

from app.repositories.observability_repository import ObservabilityRepository
from app.schemas.observability import (
    ObservabilityCountItem,
    ObservabilityMetricItem,
    ObservabilitySummaryResponse,
)
from app.services.intake_validation_service import IntakeValidationService


class ObservabilityService:
    def __init__(self) -> None:
        self.repository = ObservabilityRepository()
        self.intake_validation_service = IntakeValidationService()

    def get_summary(self, db: Session) -> ObservabilitySummaryResponse:
        counts = self.repository.get_system_counts(db)
        usage_events = self.repository.get_usage_events(db)
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

        usage_metrics = self._build_pilot_usage_metrics(usage_events)

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
            pilot_usage_metrics=usage_metrics,
            most_common_blocked_fields=blocked_fields,
            most_common_missing_inputs=[
                ObservabilityCountItem(**row) for row in missing_inputs
            ],
            most_frequent_review_reasons=[
                ObservabilityCountItem(**row) for row in review_reasons
            ],
        )

    def _build_pilot_usage_metrics(self, usage_events: list[dict]) -> list[ObservabilityMetricItem]:
        intake_created = 0
        intake_validated = 0
        intake_blocked = 0
        review_item_created = 0
        export_triggered = 0

        intake_created_times: dict[str, int] = {}
        first_analysis_completed_times: dict[str, int] = {}

        for event in usage_events:
            event_type = event["event_type"]

            if event_type == "INTAKE_CREATED":
                intake_created += 1
                intake_created_times[event["entity_id"]] = event["created_utc"]

            elif event_type == "INTAKE_VALIDATED":
                intake_validated += 1

            elif event_type == "INTAKE_BLOCKED":
                intake_blocked += 1

            elif event_type == "REVIEW_ITEM_CREATED":
                review_item_created += 1

            elif event_type == "EXPORT_TRIGGERED":
                export_triggered += 1

            elif event_type == "ANALYSIS_COMPLETED":
                payload = event.get("event_payload") or {}
                intake_id = payload.get("intake_id")
                if intake_id and intake_id not in first_analysis_completed_times:
                    first_analysis_completed_times[intake_id] = event["created_utc"]

        validation_attempts = intake_validated + intake_blocked

        intake_completion_rate = (
            (intake_validated / intake_created) * 100
            if intake_created > 0
            else 0.0
        )
        blocked_validation_rate = (
            (intake_blocked / validation_attempts) * 100
            if validation_attempts > 0
            else 0.0
        )

        successful_analysis_durations: list[int] = []
        for intake_id, completed_utc in first_analysis_completed_times.items():
            created_utc = intake_created_times.get(intake_id)
            if created_utc is not None and completed_utc >= created_utc:
                successful_analysis_durations.append(completed_utc - created_utc)

        if successful_analysis_durations:
            average_seconds = round(
                sum(successful_analysis_durations) / len(successful_analysis_durations)
            )
            time_to_first_success = f"{average_seconds}s avg"
        else:
            time_to_first_success = "N/A"

        return [
            ObservabilityMetricItem(
                label="Intake Completion Rate",
                value=f"{intake_completion_rate:.0f}%",
            ),
            ObservabilityMetricItem(
                label="Blocked Validation Rate",
                value=f"{blocked_validation_rate:.0f}%",
            ),
            ObservabilityMetricItem(
                label="Time to First Successful Analysis",
                value=time_to_first_success,
            ),
            ObservabilityMetricItem(
                label="Review Item Creation Rate",
                value=str(review_item_created),
            ),
            ObservabilityMetricItem(
                label="Export Usage Rate",
                value=str(export_triggered),
            ),
        ]