import { describe, expect, it, vi, beforeEach } from "vitest";
import { fetchWatchlist, addWatchlistItem, patchWatchlistItem, deleteWatchlistItem } from "./watchlist";
import type { WatchlistItem } from "../types/watchlist";

const item: WatchlistItem = {
  id: 1,
  symbol: "AAPL",
  note: "bullish",
  target_price: 200,
  created_at: "2024-06-01T12:00:00Z",
};

describe("watchlist API", () => {
  beforeEach(() => vi.restoreAllMocks());

  it("fetchWatchlist GETs /api/watchlist", async () => {
    const spy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify([item]), { status: 200 }),
    );
    const result = await fetchWatchlist();
    expect(spy).toHaveBeenCalledWith("/api/watchlist", expect.objectContaining({ method: "GET" }));
    expect(result).toHaveLength(1);
    expect(result[0].symbol).toBe("AAPL");
  });

  it("addWatchlistItem POSTs and returns the created item", async () => {
    const spy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify(item), { status: 201 }),
    );
    const result = await addWatchlistItem({ symbol: "AAPL" });
    expect(spy).toHaveBeenCalledWith(
      "/api/watchlist",
      expect.objectContaining({ method: "POST", body: JSON.stringify({ symbol: "AAPL" }) }),
    );
    expect(result.id).toBe(1);
  });

  it("patchWatchlistItem PATCHes the right id", async () => {
    const spy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ ...item, note: "updated" }), { status: 200 }),
    );
    await patchWatchlistItem(1, { note: "updated" });
    expect(spy).toHaveBeenCalledWith("/api/watchlist/1", expect.objectContaining({ method: "PATCH" }));
  });

  it("deleteWatchlistItem DELETEs the right id", async () => {
    const spy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(null, { status: 204 }),
    );
    await deleteWatchlistItem(42);
    expect(spy).toHaveBeenCalledWith("/api/watchlist/42", expect.objectContaining({ method: "DELETE" }));
  });
});
