import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../api/watchlist", () => ({
  fetchWatchlist: vi.fn(),
  addWatchlistItem: vi.fn(),
  patchWatchlistItem: vi.fn(),
  deleteWatchlistItem: vi.fn(),
}));

import { fetchWatchlist, addWatchlistItem, deleteWatchlistItem } from "../api/watchlist";
import { useWatchlistStore } from "./watchlistStore";
import type { WatchlistItem } from "../types/watchlist";

const item: WatchlistItem = {
  id: 1,
  symbol: "AAPL",
  note: null,
  target_price: null,
  created_at: "2024-06-01T12:00:00Z",
};

describe("useWatchlistStore", () => {
  beforeEach(() => {
    useWatchlistStore.setState({ items: [], loading: false, error: null });
    vi.clearAllMocks();
  });

  it("load() stores the response", async () => {
    vi.mocked(fetchWatchlist).mockResolvedValueOnce([item]);
    await useWatchlistStore.getState().load();
    expect(useWatchlistStore.getState().items).toHaveLength(1);
    expect(useWatchlistStore.getState().loading).toBe(false);
  });

  it("load() stores error on failure", async () => {
    vi.mocked(fetchWatchlist).mockRejectedValueOnce(new Error("net"));
    await useWatchlistStore.getState().load();
    expect(useWatchlistStore.getState().error).toBe("net");
  });

  it("add() prepends the new item", async () => {
    vi.mocked(addWatchlistItem).mockResolvedValueOnce({ ...item, symbol: "MSFT", id: 2 });
    useWatchlistStore.setState({ items: [item] });
    await useWatchlistStore.getState().add({ symbol: "MSFT" });
    const items = useWatchlistStore.getState().items;
    expect(items[0].symbol).toBe("MSFT");
    expect(items).toHaveLength(2);
  });

  it("remove() filters out the deleted id", async () => {
    vi.mocked(deleteWatchlistItem).mockResolvedValueOnce(undefined);
    useWatchlistStore.setState({ items: [item] });
    await useWatchlistStore.getState().remove(1);
    expect(useWatchlistStore.getState().items).toHaveLength(0);
  });
});
