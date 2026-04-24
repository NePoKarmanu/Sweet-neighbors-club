
export interface User {
  id: number;
  email: string;
  phone: string;
  is_staff: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
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