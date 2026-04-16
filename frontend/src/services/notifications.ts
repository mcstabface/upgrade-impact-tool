import { apiGet } from "./api";

export type NotificationItem = {
  notification_id: string;
  notification_type: string;
  severity: string;
  headline: string;
  message: string;
  target_path: string;
};

export type NotificationSummaryResponse = {
  unread_count: number;
  items: NotificationItem[];
};

export function getNotifications() {
  return apiGet<NotificationSummaryResponse>("/notifications");
}