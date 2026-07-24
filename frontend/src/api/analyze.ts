import type { AnalyzeEventHandlers } from "../types/analyze";

const BASE = import.meta.env.VITE_API_BASE ?? "";

/** Parse one SSE frame into [event, data]. Returns null if frame is malformed. */
function parseFrame(frame: string): { event: string; data: string } | null {
  let event = "message";
  let dataLine = "";
  for (const line of frame.split("\n")) {
    if (line.startsWith("event:")) event = line.slice(6).trim();
    else if (line.startsWith("data:")) dataLine = line.slice(5).trim();
  }
  if (!event) return null;
  return { event, data: dataLine };
}

function dispatch(event: string, data: string, h: AnalyzeEventHandlers): void {
  let parsed: unknown = undefined;
  if (data) {
    try {
      parsed = JSON.parse(data);
    } catch {
      parsed = data;
    }
  }
  const obj = (parsed ?? {}) as Record<string, unknown>;
  switch (event) {
    case "step":
      h.onStep?.(Number(obj.index));
      break;
    case "tool_call":
      h.onToolCall?.(String(obj.id), String(obj.name), obj.arguments);
      break;
    case "tool_result":
      h.onToolResult?.(String(obj.id), String(obj.name), Boolean(obj.ok), obj.result);
      break;
    case "final":
      h.onFinal?.(String(obj.answer ?? ""));
      break;
    case "error":
      h.onError?.(String(obj.message ?? "unknown error"));
      break;
    case "done":
      h.onDone?.();
      break;
    default:
      // Unknown event type — ignore silently rather than throw.
      break;
  }
}

/** POST /api/analyze and stream SSE events to handlers. */
export async function streamAnalyze(
  prompt: string,
  handlers: AnalyzeEventHandlers,
  signal?: AbortSignal,
): Promise<void> {
  const resp = await fetch(`${BASE}/api/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt, stream: true }),
    signal,
  });
  if (!resp.ok || !resp.body) {
    throw new Error(`analyze failed: ${resp.status} ${resp.statusText}`);
  }

  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let idx: number;
    while ((idx = buffer.indexOf("\n\n")) >= 0) {
      const frame = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      const parsed = parseFrame(frame);
      if (parsed) dispatch(parsed.event, parsed.data, handlers);
    }
  }
}
