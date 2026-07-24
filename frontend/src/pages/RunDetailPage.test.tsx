// @vitest-environment jsdom
import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";

const loadDetailMock = vi.fn(async () => {});

let holder: Record<string, unknown> = {};
function setHolder(overrides: Record<string, unknown> = {}) {
  holder = {
    detail: null,
    detailLoading: false,
    detailError: null,
    list: [],
    listLoading: false,
    listError: null,
    loadDetail: loadDetailMock,
    ...overrides,
  };
}

vi.mock("../stores/runsStore", () => ({
  useRunsStore: () => holder,
}));

import { RunDetailPage } from "./RunDetailPage";

function renderPage(route = "/runs/1") {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <Routes>
        <Route path="/runs/:id" element={<RunDetailPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("RunDetailPage", () => {
  beforeEach(() => {
    setHolder();
    vi.clearAllMocks();
  });

  it("loads the detail for the route id on mount", () => {
    renderPage("/runs/42");
    expect(loadDetailMock).toHaveBeenCalledWith(42);
  });

  it("renders a loading message while fetching", () => {
    setHolder({ detailLoading: true });
    renderPage();
    expect(screen.getByText("Loading run…")).toBeTruthy();
  });

  it("renders an error message", () => {
    setHolder({ detailError: "run not found" });
    renderPage();
    expect(screen.getByText("run not found")).toBeTruthy();
  });

  it("renders metrics and the equity chart when detail is present", () => {
    setHolder({
      detail: {
        id: 1,
        symbol: "AAPL",
        strategy_name: "sma_cross",
        strategy_params: { fast: 5, slow: 20 },
        timeframe: "1d",
        cost_bps: 1,
        n_bars: 252,
        period_start: "2024-01-01T00:00:00Z",
        period_end: "2024-12-31T00:00:00Z",
        total_return: 0.12,
        cagr: 0.15,
        sharpe: 1.1,
        max_drawdown: -0.08,
        win_rate: 0.5,
        n_trades: 7,
        equity: [
          { ts: "2024-01-01T00:00:00Z", equity: 1.0 },
          { ts: "2024-12-31T00:00:00Z", equity: 1.12 },
        ],
        created_at: "2024-06-01T12:00:00Z",
      },
    });
    renderPage();
    expect(screen.getByText("Total Return")).toBeTruthy();
    expect(screen.getByText("+12.00%")).toBeTruthy();
    expect(screen.getByRole("img", { name: /equity curve/i })).toBeTruthy();
    expect(screen.getByText(/"fast":5/)).toBeTruthy();
  });
});
