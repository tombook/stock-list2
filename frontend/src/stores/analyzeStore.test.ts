import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../api/analyze", () => ({
  streamAnalyze: vi.fn(),
}));

// `toast` from sonner touches the DOM; stub it so the node-env test stays pure.
vi.mock("sonner", () => ({
  toast: { error: vi.fn(), success: vi.fn(), info: vi.fn() },
}));

import { streamAnalyze } from "../api/analyze";
import { useAnalyzeStore } from "./analyzeStore";

// Drive streamAnalyze by calling the handlers object passed to it.
async function fire(handlerName: string, payload: unknown[]) {
  await Promise.resolve();
  const call = vi.mocked(streamAnalyze).mock.calls.at(-1);
  if (!call) throw new Error("streamAnalyze was not called");
  const handlers = call[1] as Record<string, (...a: unknown[]) => void>;
  handlers[handlerName]?.(...payload);
}

describe("useAnalyzeStore", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAnalyzeStore.getState().reset();
  });

  it("send pushes a user message and sets isStreaming", async () => {
    vi.mocked(streamAnalyze).mockImplementation(async () => {
      // no events; the test sets final state manually
    });
    const p = useAnalyzeStore.getState().send("hello");
    expect(useAnalyzeStore.getState().isStreaming).toBe(true);
    expect(useAnalyzeStore.getState().messages[0]).toMatchObject({ kind: "user", text: "hello" });
    await p;
  });

  it("onToolCall then onToolResult updates the same tool card", async () => {
    vi.mocked(streamAnalyze).mockImplementation(async () => {});
    const p = useAnalyzeStore.getState().send("hi");
    await fire("onToolCall", ["c1", "get_quote", { symbol: "AAPL" }]);
    await fire("onToolResult", ["c1", "get_quote", true, { price: 123 }]);
    await p;
    const tool = useAnalyzeStore.getState().messages.find((m) => m.kind === "tool");
    expect(tool).toMatchObject({ id: "c1", name: "get_quote", ok: true, result: { price: 123 } });
  });

  it("onFinal pushes an assistant message and clears streaming", async () => {
    vi.mocked(streamAnalyze).mockImplementation(async () => {});
    const p = useAnalyzeStore.getState().send("hi");
    await fire("onFinal", ["AAPL is at 123"]);
    await p;
    const state = useAnalyzeStore.getState();
    expect(state.isStreaming).toBe(false);
    const asst = state.messages.find((m) => m.kind === "assistant");
    expect(asst).toMatchObject({ kind: "assistant", text: "AAPL is at 123" });
  });

  it("onError pushes an assistant error message", async () => {
    vi.mocked(streamAnalyze).mockImplementation(async () => {});
    const p = useAnalyzeStore.getState().send("hi");
    await fire("onError", ["boom"]);
    await p;
    const asst = useAnalyzeStore.getState().messages.find((m) => m.kind === "assistant");
    expect(asst).toMatchObject({ kind: "assistant", text: "boom", error: true });
  });

  it("abort calls the abort controller", async () => {
    vi.mocked(streamAnalyze).mockImplementation(async () => {});
    const p = useAnalyzeStore.getState().send("hi");
    const before = useAnalyzeStore.getState();
    expect(before.abort).toBeInstanceOf(Function);
    before.abort();
    await p;
    // After abort + the mocked stream resolving, store should not be streaming.
    expect(useAnalyzeStore.getState().isStreaming).toBe(false);
  });
});
