import { describe, expect, it, vi, beforeEach } from "vitest";
import { runBacktest } from "./backtest";
import type { BacktestRequest } from "../types/backtest";

const fixture: BacktestRequest = {
  symbol: "AAPL",
  strategy: { name: "sma_cross", params: { fast: 5, slow: 20 } },
  timeframe: "1d",
  limit: 252,
  cost_bps: 0,
};

const response = {
  symbol: "AAPL",
  strategy: { name: "sma_cross", params: { fast: 5, slow: 20 } },
  timeframe: "1d",
  n_bars: 252,
  start: "2024-01-01T00:00:00",
  end: "2024-12-31T00:00:00",
  metrics: {
    total_return: 0.12,
    cagr: 0.12,
    sharpe: 1.1,
    max_drawdown: -0.08,
    win_rate: 0.55,
    n_trades: 10,
  },
  equity: [{ ts: "2024-01-01T00:00:00", equity: 1.0 }],
};

describe("runBacktest", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("POSTs the request body to /api/backtest and returns parsed JSON", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify(response), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    );

    const result = await runBacktest(fixture);

    expect(fetchSpy).toHaveBeenCalledWith(
      "/api/backtest",
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(fixture),
      }),
    );
    // 60s 超时应被传递（避免回测被默认 15s 截断）
    const opts = fetchSpy.mock.calls[0][1] as { signal?: AbortSignal };
    expect(opts.signal).toBeInstanceOf(AbortSignal);
    expect(result.metrics.total_return).toBe(0.12);
    expect(result.equity).toHaveLength(1);
  });

  it("throws ApiError on non-2xx with the server message", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ error: "unknown strategy: foo" }), {
        status: 400,
        headers: { "content-type": "application/json" },
      }),
    );
    await expect(runBacktest(fixture)).rejects.toThrow("unknown strategy: foo");
  });
});
