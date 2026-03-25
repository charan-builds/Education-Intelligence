export type PlatformNotification = {
  id: number;
  notification_type: string;
  severity: string;
  title: string;
  message: string;
  action_url?: string | null;
  created_at: string;
  read_at?: string | null;
};

export type NotificationListResponse = {
  notifications: PlatformNotification[];
};
