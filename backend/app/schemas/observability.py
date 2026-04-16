from pydantic import BaseModel


class ObservabilityCountItem(BaseModel):
    label: str
    value: int


class ObservabilitySummaryResponse(BaseModel):
    system_health_status: str
    counts: list[ObservabilityCountItem]
    most_common_blocked_fields: list[ObservabilityCountItem]
    most_common_missing_inputs: list[ObservabilityCountItem]
    most_frequent_review_reasons: list[ObservabilityCountItem]