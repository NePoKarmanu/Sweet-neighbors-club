
export interface User {
  id: number;
  email: string;
  phone: string;
  is_staff: boolean;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface RefreshTokenResponse {
  access_token: string;
  token_type: string;
}

export interface ApiError {
  detail: string;
}

export interface ListingData {
  creator_type: 'agency' | 'owner' | null;
  build_year: number | null;
  has_repair: boolean | null;
  property_type: string | null;
  living_conditions: string[];
}

export interface Listing {
  id: number;
  aggregator_id: number;
  external_id: string;
  url: string;
  image_url: string | null;
  published_at: string | null;
  parsed_at: string | null;
  title: string;
  price: number | null;
  rooms: number | null;
  area: number | null;
  floor: number | null;
  data: ListingData;
}

export interface ListingListResponse {
  items: Listing[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface ListingSearchDTO {
  property_types?: string[];
  creator_types?: Array<'agency' | 'owner'>;
  living_conditions?: string[];
  has_repair?: boolean;
  price?: { min?: number; max?: number };
  area?: { min?: number; max?: number };
  rooms?: { min?: number; max?: number };
  floor?: { min?: number; max?: number };
  build_year?: { min?: number; max?: number };
}

export type ListingSortBy = 'published_at' | 'price';
export type ListingSortOrder = 'asc' | 'desc';

export interface NotificationSettingsPayload {
  city: string;
  notify_email: boolean;
  notify_push: boolean;
}

export interface NotificationSettingsResponse {
  subscription_id: number;
  filter_id: number;
  notify_email: boolean;
  notify_push: boolean;
  is_active: boolean;
}

export interface PushSubscriptionPayload {
  endpoint: string;
  p256dh: string;
  auth: string;
  user_agent?: string;
}

export interface PushSubscriptionResponse {
  id: number;
  endpoint: string;
  is_active: boolean;
}
