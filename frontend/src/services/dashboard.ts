import { apiGet } from "./api";

export type DashboardAnalysisItem = {
  analysis_id: string;
  customer_name: string;
  environment_name: string;
  analysis_date: number | null;
  overall_status: string;
  previous_analysis_id: string | null;
  stale_reason: string | null;
  stale_detected_utc: number | null;
  applications_count: number;
  applies_count: number;
  review_required_count: number;
  unknown_count: number;
  blocked_count: number;
};

export type DashboardResponse = {
  analyses: DashboardAnalysisItem[];
  top_risks: string[];
  top_actions: string[];
  review_item_summary: {
    open_count: number;
    in_progress_count: number;
    deferred_count: number;
    overdue_count: number;
  };
};

export function getDashboard() {
  return apiGet<DashboardResponse>("/dashboard");
}