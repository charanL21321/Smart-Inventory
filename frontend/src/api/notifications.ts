import { apiClient } from './client';
import {
  Notification,
  NotificationPriority,
  NotificationType,
  UnreadCountResponse,
} from '../types';

export interface NotificationFilterParams {
  is_read?: boolean;
  notification_type?: NotificationType;
  priority?: NotificationPriority;
  skip?: number;
  limit?: number;
}

export const notificationApi = {
  getAll: (params?: NotificationFilterParams) =>
    apiClient.get<Notification[]>('/notifications', { params }),

  getUnreadCount: () =>
    apiClient.get<UnreadCountResponse>('/notifications/unread-count'),

  getById: (id: number) =>
    apiClient.get<Notification>(`/notifications/${id}`),

  markAsRead: (id: number) =>
    apiClient.patch<Notification>(`/notifications/${id}/read`),

  markAllAsRead: () =>
    apiClient.patch<{ marked_read: number }>('/notifications/read-all'),
};
