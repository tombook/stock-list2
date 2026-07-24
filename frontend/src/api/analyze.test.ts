import { describe, expect, it, vi, beforeEach } from "vitest";
import { streamAnalyze } from "./analyze";

/** Build a fake ReadableStream from a canned SSE byte string. */
function fakeStream(chunks: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  return new ReadableStream({
    start(controller) {
      for (const c of chunks) controller.enqueue(encoder.encode(c));
      controller.close();
    },
  });
}

describe("streamAnalyze", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("dispatches one handler per SSE frame", async () => {
    const body = fakeStream([
      'event: tool_call\ndata: {"id":"c1","name":"get_quote","arguments":{"symbol":"AAPL"}}\n\n',
      'event: tool_result\ndata: {"id":"c1","name":"get_quote","ok":true,"result":{"price":123}}\n\n',
      'event: step\ndata: {"index":1}\n\n',
      'event: final\ndata: {"answer":"AAPL is at 123"}\n\n',
      "event: done\ndata: {}\n\n",
    ]);
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(body, { status: 200, headers: { "content-type": "text/event-stream" } }),
    );

    const handlers = {
      onStep: vi.fn(),
      onToolCall: vi.fn(),
      onToolResult: vi.fn(),
      onFinal: vi.fn(),
      onError: vi.fn(),
      onDone: vi.fn(),
    };
    await streamAnalyze("hi", handlers);

    expect(handlers.onToolCall).toHaveBeenCalledWith("c1", "get_quote", { symbol: "AAPL" });
    expect(handlers.onToolResult).toHaveBeenCalledWith("c1", "get_quote", true, { price: 123 });
    expect(handlers.onStep).toHaveBeenCalledWith(1);
    expect(handlers.onFinal).toHaveBeenCalledWith("AAPL is at 123");
    expect(handlers.onError).not.toHaveBeenCalled();
    expect(handlers.onDone).toHaveBeenCalled();
  });

  it("invokes onError for error frames", async () => {
    const body = fakeStream(['event: error\ndata: {"message":"boom"}\n\n']);
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(body, { status: 200 }));
    const onError = vi.fn();
    await streamAnalyze("hi", { onError });
    expect(onError).toHaveBeenCalledWith("boom");
  });

  it("ignores malformed frames without throwing", async () => {
    const body = fakeStream(["garbage line with no event\n\n", "event: final\ndata: {}\n\n"]);
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(body, { status: 200 }));
    await expect(streamAnalyze("hi", {})).resolves.toBeUndefined();
  });

  it("sends the prompt as JSON body and uses POST", async () => {
    const body = fakeStream(["event: done\ndata: {}\n\n"]);
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(body));
    await streamAnalyze("hello", {});
    expect(fetchSpy).toHaveBeenCalledWith(
      "/api/analyze",
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: "hello", stream: true }),
      }),
    );
  });
});
