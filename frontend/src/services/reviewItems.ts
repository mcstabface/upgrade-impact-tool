import { apiGet, apiPatch, apiPost } from "./api";

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

export type ReviewItemUpdateRequest = {
  review_status?: string;
  assigned_owner_user_id?: string;
  due_date?: string;
  resolution_note?: string;
  defer_reason?: string;
};

export type ReviewItemUpdateResponse = {
  review_item_id: number;
  review_status: string;
  assigned_owner_user_id: string;
  due_date: string;
  updated_utc: number;
  assignment_updated_utc: number | null;
  resolution_note: string | null;
  defer_reason: string | null;
};

export type ReviewItemDetailResponse = {
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
  created_by_user_id: string;
  assignment_updated_utc: number | null;
  resolution_note: string | null;
  defer_reason: string | null;
};

export function createReviewItem(payload: ReviewItemCreateRequest) {
  return apiPost<ReviewItemCreateResponse, ReviewItemCreateRequest>(
    "/review-items",
    payload,
  );
}

export function getReviewItem(reviewItemId: number) {
  return apiGet<ReviewItemDetailResponse>(`/review-items/${reviewItemId}`);
}

export function updateReviewItem(reviewItemId: number, payload: ReviewItemUpdateRequest) {
  return apiPatch<ReviewItemUpdateResponse, ReviewItemUpdateRequest>(
    `/review-items/${reviewItemId}`,
    payload,
  );
}