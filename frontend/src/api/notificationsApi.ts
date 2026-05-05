import authClient from './authClient';
import type {
  NotificationSettingsPayload,
  NotificationSettingsResponse,
  PushSubscriptionPayload,
  PushSubscriptionResponse,
} from '../types';

export async function createNotificationSettings(
  payload: NotificationSettingsPayload,
): Promise<NotificationSettingsResponse> {
  const { data } = await authClient.post<NotificationSettingsResponse>('/notifications', payload);
  return data;
}

export async function createPushSubscription(
  payload: PushSubscriptionPayload,
): Promise<PushSubscriptionResponse> {
  const { data } = await authClient.post<PushSubscriptionResponse>('/notifications/push-subscriptions', payload);
  return data;
}

export async function deletePushSubscription(subscriptionId: number): Promise<void> {
  await authClient.delete(`/notifications/push-subscriptions/${subscriptionId}`);
}
