import { apiClient } from "@/services/apiClient";
import type { NotificationListResponse, PlatformNotification } from "@/types/notification";

export async function getNotifications(unreadOnly = false): Promise<NotificationListResponse> {
  const { data } = await apiClient.get<NotificationListResponse>("/notifications", {
    params: unreadOnly ? { unread_only: true } : undefined,
  });
  return data;
}

export async function markNotificationRead(notificationId: number): Promise<PlatformNotification> {
  const { data } = await apiClient.post<PlatformNotification>(`/notifications/${notificationId}/read`);
  return data;
}
