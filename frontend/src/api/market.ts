import { request } from "./client";
import type { Bars, Quote } from "../types/market";

export function fetchQuote(symbol: string): Promise<Quote> {
  return request<Quote>(`/api/quote/${encodeURIComponent(symbol.toUpperCase())}`);
}

export function fetchBars(symbol: string, timeframe = "1d", limit = 120): Promise<Bars> {
  const params = new URLSearchParams({ timeframe, limit: String(limit) });
  return request<Bars>(`/api/bars/${encodeURIComponent(symbol.toUpperCase())}?${params}`);
}
