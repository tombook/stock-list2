/** WebSocket hook for real-time quote streaming. */

import { useEffect, useRef, useState } from "react";

export interface Quote {
  symbol: string;
  price?: number;
  change_pct?: number | null;
  source?: string;
  error?: string;
}

export interface QuotesMessage {
  type: "hello" | "quotes" | "subscribed";
  symbols?: string[];
  data?: Record<string, Quote>;
  push_interval_seconds?: number;
}

export function useQuotesWS(_initialSymbols: string[]): {
  quotes: Record<string, Quote>;
  connected: boolean;
  subscribe: (symbols: string[]) => void;
  unsubscribe: (symbols: string[]) => void;
} {
  const [quotes, setQuotes] = useState<Record<string, Quote>>({});
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    const url = `${protocol}//${host}/ws/quotes`;

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);
    ws.onmessage = (event) => {
      try {
        const msg: QuotesMessage = JSON.parse(event.data);
        if (msg.type === "quotes" && msg.data) {
          setQuotes(msg.data);
        }
      } catch {
        // ignore malformed messages
      }
    };

    return () => {
      ws.close();
    };
  }, []);

  const subscribe = (symbols: string[]) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: "subscribe", symbols }));
    }
  };

  const unsubscribe = (symbols: string[]) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: "unsubscribe", symbols }));
    }
  };

  return { quotes, connected, subscribe, unsubscribe };
}
