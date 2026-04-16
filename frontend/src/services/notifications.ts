import { apiGet, apiPatch } from "./api";

export type NotificationItem = {
  notification_id: string;
  notification_type: string;
  severity: string;
  headline: string;
  message: string;
  target_path: string;
  is_read: boolean;
};

export type NotificationSummaryResponse = {
  unread_count: number;
  items: NotificationItem[];
};

export type NotificationReadResponse = {
  notification_id: string;
  is_read: boolean;
  updated_utc: number;
};

export function getNotifications() {
  return apiGet<NotificationSummaryResponse>("/notifications");
}

export function markNotificationRead(notificationId: string) {
  return apiPatch<NotificationReadResponse, Record<string, never>>(
    `/notifications/${notificationId}/read`,
    {},
  );
}