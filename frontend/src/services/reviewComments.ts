import { apiGet, apiPost } from "./api";

export type ReviewComment = {
  comment_id: number;
  review_item_id: number;
  comment_text: string;
  created_by_user_id: string;
  created_utc: number;
};

export type ReviewCommentListResponse = {
  items: ReviewComment[];
};

export type ReviewCommentCreateRequest = {
  comment_text: string;
  created_by_user_id: string;
};

export function getReviewComments(reviewItemId: number) {
  return apiGet<ReviewCommentListResponse>(`/review-items/${reviewItemId}/comments`);
}

export function createReviewComment(
  reviewItemId: number,
  payload: ReviewCommentCreateRequest,
) {
  return apiPost<ReviewComment, ReviewCommentCreateRequest>(
    `/review-items/${reviewItemId}/comments`,
    payload,
  );
}