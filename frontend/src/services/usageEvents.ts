import { apiPostNoContent } from "./api";

export type ResultsOverviewSessionEventRequest = {
  analysis_id: string;
  duration_seconds: number;
};

export function recordResultsOverviewSession(
  payload: ResultsOverviewSessionEventRequest,
): Promise<void> {
  return apiPostNoContent("/usage-events/results-overview-session", payload);
}