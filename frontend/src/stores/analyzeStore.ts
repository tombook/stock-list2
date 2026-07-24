import { create } from "zustand";
import { toast } from "sonner";
import { streamAnalyze } from "../api/analyze";
import type { AnalyzeEventHandlers, ChatMessage } from "../types/analyze";

interface AnalyzeState {
  messages: ChatMessage[];
  isStreaming: boolean;
  step: number | null;
  send: (prompt: string) => Promise<void>;
  abort: () => void;
  reset: () => void;
}

let _idCounter = 0;
function nextId(prefix: string): string {
  _idCounter += 1;
  return `${prefix}-${_idCounter}`;
}

export const useAnalyzeStore = create<AnalyzeState>((set) => {
  let controller: AbortController | null = null;

  const handlers: AnalyzeEventHandlers = {
    onStep: (index) => set({ step: index }),
    onToolCall: (id, name, args) =>
      set((s) => ({
        messages: [
          ...s.messages,
          { kind: "tool" as const, id, name, args },
        ],
      })),
    onToolResult: (id, _name, ok, result) =>
      set((s) => ({
        messages: s.messages.map((m) =>
          m.kind === "tool" && m.id === id ? { ...m, ok, result } : m,
        ),
      })),
    onFinal: (answer) =>
      set((s) => ({
        messages: [...s.messages, { kind: "assistant" as const, id: nextId("a"), text: answer }],
        isStreaming: false,
        step: null,
      })),
    onError: (message) => {
      toast.error(message);
      set((s) => ({
        messages: [
          ...s.messages,
          { kind: "assistant" as const, id: nextId("a"), text: message, error: true },
        ],
        isStreaming: false,
        step: null,
      }));
    },
    onDone: () => set({ isStreaming: false, step: null }),
  };

  return {
    messages: [],
    isStreaming: false,
    step: null,

    send: async (prompt) => {
      controller = new AbortController();
      set((s) => ({
        messages: [
          ...s.messages,
          { kind: "user" as const, id: nextId("u"), text: prompt },
        ],
        isStreaming: true,
        step: null,
      }));
      try {
        await streamAnalyze(prompt, handlers, controller.signal);
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        const aborted =
          (e instanceof DOMException && e.name === "AbortError") || msg === "AbortError";
        if (!aborted) handlers.onError?.(msg);
      } finally {
        controller = null;
        set({ isStreaming: false, step: null });
      }
    },

    abort: () => {
      controller?.abort();
      controller = null;
      set({ isStreaming: false, step: null });
    },

    reset: () => {
      controller?.abort();
      controller = null;
      set({ messages: [], isStreaming: false, step: null });
    },
  };
});
