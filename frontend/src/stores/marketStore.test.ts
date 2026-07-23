import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../api/market", () => ({
  fetchQuote: vi.fn(),
  fetchBars: vi.fn(),
}));

import { fetchBars, fetchQuote } from "../api/market";
import { useMarketStore } from "./marketStore";

const quoteFixture = {
  symbol: "AAPL",
  price: 100,
  currency: "USD",
  name: null,
  change_pct: null,
  as_of: null,
  source: "test",
};
const barsFixture = { symbol: "AAPL", timeframe: "1d", bars: [], source: "test" };

describe("useMarketStore", () => {
  beforeEach(() => {
    useMarketStore.setState({ quote: null, bars: null, loading: false, error: null });
    vi.clearAllMocks();
    vi.mocked(fetchQuote).mockResolvedValue(quoteFixture);
    vi.mocked(fetchBars).mockResolvedValue(barsFixture);
  });

  it("lookup populates quote and bars", async () => {
    await useMarketStore.getState().lookup("aapl");
    expect(fetchQuote).toHaveBeenCalledWith("aapl");
    const state = useMarketStore.getState();
    expect(state.quote?.price).toBe(100);
    expect(state.bars?.bars).toEqual([]);
    expect(state.loading).toBe(false);
    expect(state.error).toBeNull();
  });

  it("lookup stores the error message on failure", async () => {
    vi.mocked(fetchQuote).mockRejectedValueOnce(new Error("boom"));
    await useMarketStore.getState().lookup("AAPL");
    expect(useMarketStore.getState().error).toBe("boom");
    expect(useMarketStore.getState().loading).toBe(false);
  });
});
