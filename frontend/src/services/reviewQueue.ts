import { apiGet } from "./api";

export type ReviewQueueItem = {
  review_item_id: number;
  finding_id: number;
  analysis_id: string;
  application_name: string;
  finding_headline: string;
  kb_reference: string;
  review_reason: string;
  assigned_owner_user_id: string;
  due_date: string;
  review_status: string;
  created_utc: number;
  updated_utc: number;
  resolution_note: string | null;
  defer_reason: string | null;
};

export type ReviewQueueResponse = {
  items: ReviewQueueItem[];
};

export function getReviewQueue() {
  return apiGet<ReviewQueueResponse>("/review-queue");
}