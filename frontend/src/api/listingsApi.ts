import axios from 'axios';
import type { ListingListResponse, ListingSearchDTO, ListingSortBy, ListingSortOrder } from '../types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface FetchListingsParams {
  limit: number;
  offset: number;
  search?: ListingSearchDTO;
  sort_by?: ListingSortBy;
  sort_order?: ListingSortOrder;
}

export async function fetchListings({
  limit,
  offset,
  search,
  sort_by,
  sort_order,
}: FetchListingsParams): Promise<ListingListResponse> {
  const params: Record<string, string | number> = {
    limit,
    offset,
  };

  if (search && Object.keys(search).length > 0) {
    params.search = JSON.stringify(search);
  }
  if (sort_by && sort_order) {
    params.sort_by = sort_by;
    params.sort_order = sort_order;
  }

  const { data } = await axios.get<ListingListResponse>(`${API_BASE}/listing`, { params });
  return data;
}
