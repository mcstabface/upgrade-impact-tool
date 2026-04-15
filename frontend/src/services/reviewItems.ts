import { apiPost } from "./api";

export type ReviewItemCreateRequest = {
  finding_id: number;
  review_reason: string;
  assigned_owner_user_id: string;
  due_date: string;
  created_by_user_id?: string;
};

export type ReviewItemCreateResponse = {
  review_item_id: number;
  finding_id: number;
  review_status: string;
  assigned_owner_user_id: string;
  due_date: string;
  created_utc: number;
};

export function createReviewItem(payload: ReviewItemCreateRequest) {
  return apiPost<ReviewItemCreateResponse, ReviewItemCreateRequest>(
    "/review-items",
    payload,
  );
}