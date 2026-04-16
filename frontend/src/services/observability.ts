import { apiGet } from "./api";

export type ObservabilityCountItem = {
  label: string;
  value: number;
};

export type ObservabilityMetricItem = {
  label: string;
  value: string;
};

export type ObservabilitySummaryResponse = {
  system_health_status: string;
  counts: ObservabilityCountItem[];
  pilot_usage_metrics: ObservabilityMetricItem[];
  most_common_blocked_fields: ObservabilityCountItem[];
  most_common_missing_inputs: ObservabilityCountItem[];
  most_frequent_review_reasons: ObservabilityCountItem[];
};

export function getObservabilitySummary() {
  return apiGet<ObservabilitySummaryResponse>("/observability/summary");
}