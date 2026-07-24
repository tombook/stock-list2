// @vitest-environment jsdom
import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

const sendMock = vi.fn(async () => {});
const fixedState = {
  messages: [
    { kind: "user", id: "u1", text: "hello" },
    { kind: "assistant", id: "a1", text: "hi there" },
  ],
  isStreaming: false,
  step: null,
  send: sendMock,
  abort: vi.fn(),
  reset: vi.fn(),
};

vi.mock("../stores/analyzeStore", () => ({
  // AnalyzePage calls `useAnalyzeStore()` with no selector and destructures;
  // the mock returns the whole state object.
  useAnalyzeStore: () => fixedState,
}));

import { AnalyzePage } from "./AnalyzePage";

function renderPage() {
  return render(
    <MemoryRouter>
      <AnalyzePage />
    </MemoryRouter>,
  );
}

describe("AnalyzePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders prior messages", () => {
    renderPage();
    expect(screen.getByText("hello")).toBeTruthy();
    expect(screen.getByText("hi there")).toBeTruthy();
  });

  it("submits the draft on button click", () => {
    renderPage();
    const input = screen.getByPlaceholderText(/ask/i) as HTMLTextAreaElement;
    fireEvent.change(input, { target: { value: "analyze AAPL" } });
    fireEvent.click(screen.getByRole("button", { name: /send/i }));
    expect(sendMock).toHaveBeenCalledWith("analyze AAPL");
  });
});
