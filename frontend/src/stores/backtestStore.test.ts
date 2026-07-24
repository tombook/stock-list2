import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../api/backtest", () => ({
  runBacktest: vi.fn(),
}));

import { runBacktest } from "../api/backtest";
import { useBacktestStore } from "./backtestStore";
import type { BacktestResponse } from "../types/backtest";

const okResponse: BacktestResponse = {
  symbol: "AAPL",
  strategy: { name: "sma_cross", params: { fast: 5, slow: 20 } },
  timeframe: "1d",
  n_bars: 252,
  start: "2024-01-01T00:00:00",
  end: "2024-12-31T00:00:00",
  metrics: {
    total_return: 0.1,
    cagr: 0.1,
    sharpe: 1.0,
    max_drawdown: -0.05,
    win_rate: 0.5,
    n_trades: 8,
  },
  equity: [{ ts: "2024-01-01T00:00:00", equity: 1.0 }],
};

describe("useBacktestStore", () => {
  beforeEach(() => {
    useBacktestStore.setState({
      symbol: "AAPL",
      strategyName: "sma_cross",
      params: { fast: 5, slow: 20 },
      timeframe: "1d",
      limit: 252,
      costBps: 0,
      result: null,
      loading: false,
      error: null,
    });
    vi.clearAllMocks();
  });

  it("run() sends the current form as a BacktestRequest and stores the response", async () => {
    vi.mocked(runBacktest).mockResolvedValueOnce(okResponse);
    await useBacktestStore.getState().run();
    expect(runBacktest).toHaveBeenCalledWith({
      symbol: "AAPL",
      strategy: { name: "sma_cross", params: { fast: 5, slow: 20 } },
      timeframe: "1d",
      limit: 252,
      cost_bps: 0,
    });
    const state = useBacktestStore.getState();
    expect(state.result?.metrics.total_return).toBe(0.1);
    expect(state.loading).toBe(false);
    expect(state.error).toBeNull();
  });

  it("run() stores the error message on failure", async () => {
    vi.mocked(runBacktest).mockRejectedValueOnce(new Error("boom"));
    await useBacktestStore.getState().run();
    expect(useBacktestStore.getState().error).toBe("boom");
    expect(useBacktestStore.getState().loading).toBe(false);
  });

  it("setStrategy() resets params to that strategy's defaults", () => {
    useBacktestStore.getState().setStrategy("momentum");
    expect(useBacktestStore.getState().strategyName).toBe("momentum");
    expect(useBacktestStore.getState().params).toEqual({ lookback: 20 });
  });

  it("setParam() updates a single param without dropping the others", () => {
    useBacktestStore.getState().setParam("fast", 10);
    expect(useBacktestStore.getState().params).toEqual({ fast: 10, slow: 20 });
  });
});
