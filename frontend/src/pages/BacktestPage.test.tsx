// @vitest-environment jsdom
import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

const runMock = vi.fn(async () => {});
const setStrategyMock = vi.fn();

// BacktestPage 以无选择器方式解构整个 store；mock 返回一个可替换的 holder，
// 每个用例通过 setHolder() 注入不同状态来覆盖渲染分支。
let holder: Record<string, unknown> = {};
function setHolder(overrides: Record<string, unknown> = {}) {
  holder = {
    symbol: "AAPL",
    strategyName: "sma_cross",
    params: { fast: 5, slow: 20 },
    timeframe: "1d",
    limit: 252,
    costBps: 0,
    result: null,
    loading: false,
    error: null,
    setSymbol: vi.fn(),
    setStrategy: setStrategyMock,
    setParam: vi.fn(),
    setTimeframe: vi.fn(),
    setLimit: vi.fn(),
    setCostBps: vi.fn(),
    run: runMock,
    ...overrides,
  };
}

vi.mock("../stores/backtestStore", () => ({
  useBacktestStore: () => holder,
}));

import { BacktestPage } from "./BacktestPage";

function renderPage() {
  return render(
    <MemoryRouter>
      <BacktestPage />
    </MemoryRouter>,
  );
}

describe("BacktestPage", () => {
  beforeEach(() => {
    setHolder();
    vi.clearAllMocks();
  });

  it("renders the form with symbol and a Run button", () => {
    renderPage();
    expect((screen.getByPlaceholderText("AAPL") as HTMLInputElement).value).toBe("AAPL");
    expect(screen.getByRole("button", { name: /run/i })).toBeTruthy();
  });

  it("calls run() when the form is submitted", () => {
    renderPage();
    fireEvent.click(screen.getByRole("button", { name: /run/i }));
    expect(runMock).toHaveBeenCalledOnce();
  });

  it("renders metrics and the equity chart when a result is present", () => {
    setHolder({
      result: {
        symbol: "AAPL",
        strategy: { name: "sma_cross", params: {} },
        timeframe: "1d",
        n_bars: 252,
        start: "2024-01-01T00:00:00",
        end: "2024-12-31T00:00:00",
        metrics: { total_return: 0.12, cagr: 0.15, sharpe: 1.1, max_drawdown: -0.08, win_rate: 0.5, n_trades: 7 },
        equity: [
          { ts: "2024-01-01T00:00:00", equity: 1.0 },
          { ts: "2024-06-01T00:00:00", equity: 1.06 },
          { ts: "2024-12-31T00:00:00", equity: 1.12 },
        ],
      },
    });
    renderPage();
    expect(screen.getByText("Total Return")).toBeTruthy();
    expect(screen.getByText("+12.00%")).toBeTruthy();
    expect(screen.getByRole("img", { name: /equity curve/i })).toBeTruthy();
  });
});
