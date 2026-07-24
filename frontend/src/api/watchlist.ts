import { request } from "./client";
import type { WatchlistItem, WatchlistCreate, WatchlistUpdate } from "../types/watchlist";

/** GET /api/watchlist — 获取观察列表。 */
export function fetchWatchlist(): Promise<WatchlistItem[]> {
  return request<WatchlistItem[]>("/api/watchlist");
}

/** POST /api/watchlist — 添加标的。 */
export function addWatchlistItem(body: WatchlistCreate): Promise<WatchlistItem> {
  return request<WatchlistItem>("/api/watchlist", { method: "POST", body });
}

/** PATCH /api/watchlist/:id — 更新备注/目标价。 */
export function patchWatchlistItem(id: number, body: WatchlistUpdate): Promise<WatchlistItem> {
  return request<WatchlistItem>(`/api/watchlist/${id}`, { method: "PATCH", body });
}

/** DELETE /api/watchlist/:id — 移除标的。 */
export function deleteWatchlistItem(id: number): Promise<void> {
  return request<void>(`/api/watchlist/${id}`, { method: "DELETE" });
}
