import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../api/runs", () => ({
  fetchRuns: vi.fn(),
  fetchRun: vi.fn(),
}));

import { fetchRuns, fetchRun } from "../api/runs";
import { useRunsStore } from "./runsStore";
import type { RunSummary, RunDetail } from "../types/run";

const summary: RunSummary = {
  id: 1,
  symbol: "AAPL",
  strategy_name: "sma_cross",
  timeframe: "1d",
  n_bars: 252,
  period_start: "2024-01-01T00:00:00Z",
  period_end: "2024-12-31T00:00:00Z",
  total_return: 0.1,
  sharpe: 1.0,
  max_drawdown: -0.05,
  n_trades: 3,
  created_at: "2024-06-01T12:00:00Z",
};

const detail: RunDetail = {
  ...summary,
  strategy_params: { fast: 5, slow: 20 },
  cost_bps: 0,
  cagr: 0.1,
  win_rate: 0.5,
  equity: [{ ts: "2024-01-01T00:00:00Z", equity: 1.0 }],
};

describe("useRunsStore", () => {
  beforeEach(() => {
    useRunsStore.setState({
      list: [],
      listLoading: false,
      listError: null,
      detail: null,
      detailLoading: false,
      detailError: null,
    });
    vi.clearAllMocks();
  });

  it("loadList() stores the response array", async () => {
    vi.mocked(fetchRuns).mockResolvedValueOnce([summary]);
    await useRunsStore.getState().loadList();
    expect(fetchRuns).toHaveBeenCalledOnce();
    expect(useRunsStore.getState().list).toHaveLength(1);
    expect(useRunsStore.getState().listLoading).toBe(false);
    expect(useRunsStore.getState().listError).toBeNull();
  });

  it("loadList() stores the error message on failure", async () => {
    vi.mocked(fetchRuns).mockRejectedValueOnce(new Error("network"));
    await useRunsStore.getState().loadList();
    expect(useRunsStore.getState().listError).toBe("network");
    expect(useRunsStore.getState().listLoading).toBe(false);
  });

  it("loadDetail() stores the full run", async () => {
    vi.mocked(fetchRun).mockResolvedValueOnce(detail);
    await useRunsStore.getState().loadDetail(1);
    expect(fetchRun).toHaveBeenCalledWith(1);
    expect(useRunsStore.getState().detail?.symbol).toBe("AAPL");
    expect(useRunsStore.getState().detailLoading).toBe(false);
  });

  it("loadDetail() stores the error message on failure", async () => {
    vi.mocked(fetchRun).mockRejectedValueOnce(new Error("not found"));
    await useRunsStore.getState().loadDetail(99);
    expect(useRunsStore.getState().detailError).toBe("not found");
    expect(useRunsStore.getState().detailLoading).toBe(false);
  });
});
