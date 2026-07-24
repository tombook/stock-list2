// @vitest-environment jsdom
import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

const loadListMock = vi.fn(async () => {});

let holder: Record<string, unknown> = {};
function setHolder(overrides: Record<string, unknown> = {}) {
  holder = {
    list: [],
    listLoading: false,
    listError: null,
    detail: null,
    detailLoading: false,
    detailError: null,
    loadList: loadListMock,
    ...overrides,
  };
}

vi.mock("../stores/runsStore", () => ({
  useRunsStore: () => holder,
}));

import { RunsPage } from "./RunsPage";

function renderPage() {
  return render(
    <MemoryRouter>
      <RunsPage />
    </MemoryRouter>,
  );
}

describe("RunsPage", () => {
  beforeEach(() => {
    setHolder();
    vi.clearAllMocks();
  });

  it("auto-loads the list on mount", () => {
    renderPage();
    expect(loadListMock).toHaveBeenCalled();
  });

  it("renders a loading message while fetching", () => {
    setHolder({ listLoading: true, list: [] });
    renderPage();
    expect(screen.getByText("Loading runs…")).toBeTruthy();
  });

  it("renders an empty state when there are no runs", () => {
    renderPage();
    expect(screen.getByText(/No runs yet/i)).toBeTruthy();
  });

  it("renders an error message", () => {
    setHolder({ listError: "db down" });
    renderPage();
    expect(screen.getByText("db down")).toBeTruthy();
  });

  it("renders a table with run rows and detail links", () => {
    setHolder({
      list: [
        {
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
        },
      ],
    });
    renderPage();
    expect(screen.getByText("AAPL")).toBeTruthy();
    expect(screen.getByText("sma_cross")).toBeTruthy();
    expect(screen.getByText("+12.00%")).toBeTruthy();
    expect((screen.getByRole("link", { name: "AAPL" }) as HTMLAnchorElement).href).toContain("/runs/1");
  });
});
