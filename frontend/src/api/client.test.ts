import { afterEach, describe, expect, it, vi } from "vitest";
import { request } from "./client";

const originalFetch = globalThis.fetch;

function mockResponse(body: string, status: number): Response {
  return new Response(body, { status });
}

afterEach(() => {
  globalThis.fetch = originalFetch;
});

describe("request", () => {
  it("returns parsed JSON on success", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(mockResponse('{"a":1}', 200)) as unknown as typeof fetch;
    await expect(request<{ a: number }>("/x")).resolves.toEqual({ a: 1 });
  });

  it("throws ApiError with server message on non-2xx", async () => {
    globalThis.fetch = vi
      .fn()
      .mockResolvedValue(mockResponse('{"error":"nope"}', 400)) as unknown as typeof fetch;
    await expect(request("/x")).rejects.toMatchObject({ name: "ApiError", status: 400, message: "nope" });
  });

  it("aborts after the timeout", async () => {
    globalThis.fetch = vi.fn().mockImplementation((_url, init) => {
      const signal = (init as RequestInit).signal;
      return new Promise((_resolve, reject) => {
        signal?.addEventListener("abort", () => reject(new DOMException("aborted", "AbortError")));
      });
    }) as unknown as typeof fetch;
    await expect(request("/x", { timeoutMs: 30 })).rejects.toThrow();
  });
});
