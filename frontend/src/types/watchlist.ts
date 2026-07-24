/** 镜像 backend/app/watchlist/schemas.py。 */

export interface WatchlistItem {
  id: number;
  symbol: string;
  note: string | null;
  target_price: number | null;
  created_at: string;
}

export interface WatchlistCreate {
  symbol: string;
  note?: string | null;
  target_price?: number | null;
}

export interface WatchlistUpdate {
  note?: string | null;
  target_price?: number | null;
}
