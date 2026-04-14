import { apiGet } from "./api";

export type ReviewQueueItem = {
  finding_id: number;
  analysis_id: string;
  application_name: string;
  finding_status: string;
  severity: string;
  headline: string;
  reason_for_status: string | null;
};

export type ReviewQueueResponse = {
  items: ReviewQueueItem[];
};

export function getReviewQueue() {
  return apiGet<ReviewQueueResponse>("/review-queue");
}