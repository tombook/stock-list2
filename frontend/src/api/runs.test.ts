import { describe, expect, it, vi, beforeEach } from "vitest";
import { fetchRuns, fetchRun } from "./runs";
import type { RunSummary, RunDetail } from "../types/run";

const summary: RunSummary = {
  id: 1,
  symbol: "AAPL",
  strategy_name: "sma_cross",
  timeframe: "1d",
  n_bars: 252,
  period_start: "2024-01-01T00:00:00Z",
  period_end: "2024-12-31T00:00:00Z",
  total_return: 0.12,
  sharpe: 1.1,
  max_drawdown: -0.08,
  n_trades: 5,
  created_at: "2024-06-01T12:00:00Z",
};

const detail: RunDetail = {
  ...summary,
  strategy_params: { fast: 5, slow: 20 },
  cost_bps: 1.0,
  cagr: 0.12,
  win_rate: 0.6,
  equity: [
    { ts: "2024-01-01T00:00:00Z", equity: 1.0 },
    { ts: "2024-06-01T00:00:00Z", equity: 1.06 },
  ],
};

describe("fetchRuns", () => {
  beforeEach(() => vi.restoreAllMocks());

  it("GETs /api/runs and returns parsed JSON array", async () => {
    const spy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify([summary]), { status: 200 }),
    );
    const result = await fetchRuns();
    expect(spy).toHaveBeenCalledWith("/api/runs", expect.objectContaining({ method: "GET" }));
    expect(result).toHaveLength(1);
    expect(result[0].symbol).toBe("AAPL");
  });

  it("throws ApiError on non-2xx", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ error: "db down" }), { status: 500 }),
    );
    await expect(fetchRuns()).rejects.toThrow("db down");
  });
});

describe("fetchRun", () => {
  beforeEach(() => vi.restoreAllMocks());

  it("GETs /api/runs/:id and returns the full detail", async () => {
    const spy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify(detail), { status: 200 }),
    );
    const result = await fetchRun(42);
    expect(spy).toHaveBeenCalledWith("/api/runs/42", expect.objectContaining({ method: "GET" }));
    expect(result.equity).toHaveLength(2);
    expect(result.cagr).toBe(0.12);
  });

  it("throws ApiError on 404", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "run 99 not found" }), { status: 404 }),
    );
    await expect(fetchRun(99)).rejects.toThrow();
  });
});
