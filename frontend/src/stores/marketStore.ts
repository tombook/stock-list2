import { create } from "zustand";
import { fetchBars, fetchQuote } from "../api/market";
import type { Bars, Quote } from "../types/market";

export interface MarketState {
  symbol: string;
  quote: Quote | null;
  bars: Bars | null;
  loading: boolean;
  error: string | null;
  lookup: (symbol: string) => Promise<void>;
}

export const useMarketStore = create<MarketState>((set) => ({
  symbol: "AAPL",
  quote: null,
  bars: null,
  loading: false,
  error: null,
  lookup: async (symbol) => {
    set({ loading: true, error: null });
    try {
      const [quote, bars] = await Promise.all([fetchQuote(symbol), fetchBars(symbol)]);
      set({ symbol, quote, bars, loading: false });
    } catch (e) {
      set({ loading: false, error: e instanceof Error ? e.message : String(e) });
    }
  },
}));
