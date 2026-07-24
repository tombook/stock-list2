// @vitest-environment jsdom
import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

const loadMock = vi.fn(async () => {});
const addMock = vi.fn(async () => {});
const removeMock = vi.fn(async () => {});

let holder: Record<string, unknown> = {};
function setHolder(overrides: Record<string, unknown> = {}) {
  holder = {
    items: [],
    loading: false,
    error: null,
    load: loadMock,
    add: addMock,
    patch: vi.fn(),
    remove: removeMock,
    ...overrides,
  };
}

vi.mock("../stores/watchlistStore", () => ({
  useWatchlistStore: () => holder,
}));

import { WatchlistPage } from "./WatchlistPage";

function renderPage() {
  return render(
    <MemoryRouter>
      <WatchlistPage />
    </MemoryRouter>,
  );
}

describe("WatchlistPage", () => {
  beforeEach(() => {
    setHolder();
    vi.clearAllMocks();
  });

  it("auto-loads on mount", () => {
    renderPage();
    expect(loadMock).toHaveBeenCalled();
  });

  it("renders empty state", () => {
    renderPage();
    expect(screen.getByText(/empty/i)).toBeTruthy();
  });

  it("renders error message", () => {
    setHolder({ error: "db error" });
    renderPage();
    expect(screen.getByText("db error")).toBeTruthy();
  });

  it("renders items in a table with remove buttons", () => {
    setHolder({
      items: [
        { id: 1, symbol: "AAPL", note: "bullish", target_price: null, created_at: "2024-06-01T12:00:00Z" },
        { id: 2, symbol: "MSFT", note: null, target_price: null, created_at: "2024-06-02T12:00:00Z" },
      ],
    });
    renderPage();
    expect(screen.getByText("AAPL")).toBeTruthy();
    expect(screen.getByText("bullish")).toBeTruthy();
    expect(screen.getByText("MSFT")).toBeTruthy();
    expect(screen.getAllByText("Remove")).toHaveLength(2);
  });

  it("calls remove() when Remove is clicked", () => {
    setHolder({
      items: [{ id: 5, symbol: "GOOG", note: null, target_price: null, created_at: "2024-06-01T12:00:00Z" }],
    });
    renderPage();
    fireEvent.click(screen.getByText("Remove"));
    expect(removeMock).toHaveBeenCalledWith(5);
  });
});
