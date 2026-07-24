import { type FormEvent, useEffect, useRef, useState } from "react";
import { useAnalyzeStore } from "../stores/analyzeStore";
import { MessageBubble } from "../components/chat/MessageBubble";
import { Button } from "../components/ui/Button";

const SUGGESTIONS = ["Analyze AAPL", "Backtest SMA cross on MSFT daily"];

export function AnalyzePage() {
  const { messages, isStreaming, step, send, abort } = useAnalyzeStore();
  const [draft, setDraft] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo?.({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, step]);

  const submit = (e: FormEvent) => {
    e.preventDefault();
    const text = draft.trim();
    if (!text || isStreaming) return;
    setDraft("");
    void send(text);
  };

  return (
    <div className="mx-auto flex h-full max-w-3xl flex-col">
      <div className="flex items-center justify-between pb-2">
        <h1 className="text-2xl font-bold">Analyze</h1>
        {isStreaming && (
          <Button variant="ghost" onClick={abort}>
            Stop
          </Button>
        )}
      </div>

      <div ref={scrollRef} className="flex-1 space-y-3 overflow-auto pb-4">
        {messages.length === 0 && (
          <div className="flex flex-wrap gap-2 pt-4">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => void send(s)}
                className="rounded-full border border-slate-300 px-3 py-1 text-sm text-slate-600 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-300"
              >
                {s}
              </button>
            ))}
          </div>
        )}
        {messages.map((m) => (
          <MessageBubble key={m.id} msg={m} />
        ))}
        {isStreaming && step !== null && (
          <div className="text-center text-xs text-slate-400">step {step}</div>
        )}
      </div>

      <form onSubmit={submit} className="flex gap-2 border-t border-slate-200 pt-3 dark:border-slate-800">
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submit(e);
            }
          }}
          placeholder="ask the agent…"
          rows={2}
          className="flex-1 resize-none rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
        />
        <Button type="submit" disabled={isStreaming || !draft.trim()}>
          Send
        </Button>
      </form>
    </div>
  );
}
