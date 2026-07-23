/** Typed HTTP client for the backend. Base URL comes from VITE_API_BASE (empty in dev,
 *  where Vite proxies /api and /health to the backend). */

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly body?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

const BASE = import.meta.env.VITE_API_BASE ?? "";

function extractMessage(data: unknown, fallback: string): string {
  if (data && typeof data === "object" && "error" in data) {
    const value = (data as { error: unknown }).error;
    if (typeof value === "string") return value;
  }
  return fallback;
}

export interface RequestOptions {
  method?: string;
  body?: unknown;
  timeoutMs?: number;
  signal?: AbortSignal;
}

export async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, timeoutMs = 15000, signal } = opts;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  if (signal) {
    if (signal.aborted) controller.abort();
    else signal.addEventListener("abort", () => controller.abort(), { once: true });
  }
  try {
    const resp = await fetch(`${BASE}${path}`, {
      method,
      headers: body !== undefined ? { "Content-Type": "application/json" } : undefined,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });
    const text = await resp.text();
    const data = text ? (JSON.parse(text) as unknown) : undefined;
    if (!resp.ok) {
      throw new ApiError(resp.status, extractMessage(data, resp.statusText), data);
    }
    return data as T;
  } finally {
    clearTimeout(timer);
  }
}
