import { type FormEvent, useEffect, useState } from "react";
import { useMarketStore } from "../stores/marketStore";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { PriceChart } from "../components/charts/PriceChart";
import { RSIPanel } from "../components/charts/RSIPanel";
import { MACDPanel } from "../components/charts/MACDPanel";
import { useQuotesWS } from "../hooks/useQuotesWS";

export function MarketsPage() {
  const { symbol, quote, bars, loading, error, lookup } = useMarketStore();
  const [draft, setDraft] = useState(symbol);
  const [smaPeriods, setSmaPeriods] = useState<number[]>([]);
  const [showRSI, setShowRSI] = useState(false);
  const [showMACD, setShowMACD] = useState(false);
  const { quotes: wsQuotes, connected } = useQuotesWS([symbol]);
  const liveQuote = wsQuotes[symbol.toUpperCase()];

  useEffect(() => {
    lookup(symbol);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (draft.trim()) lookup(draft.trim());
  };

  const toggleSma = (period: number) => {
    setSmaPeriods((prev) =>
      prev.includes(period) ? prev.filter((p) => p !== period) : [...prev, period],
    );
  };

  return (
    <div className="mx-auto max-w-4xl space-y-4">
      <h1 className="text-2xl font-bold">Markets</h1>

      <form onSubmit={submit} className="flex items-center gap-2">
        <Input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="AAPL"
          className="w-40 uppercase"
        />
        <Button type="submit" disabled={loading}>
          {loading ? "Loading…" : "Lookup"}
        </Button>
      </form>

      {error && <Card className="border-red-300 text-red-600">{error}</Card>}

      {quote && (
        <Card>
          <div className="flex items-baseline justify-between">
            <div>
              <div className="text-lg font-semibold">{quote.symbol}</div>
              <div className="text-3xl font-bold">
                {quote.price.toFixed(2)} <span className="text-base text-slate-500">{quote.currency ?? ""}</span>
              </div>
            </div>
            {quote.change_pct !== null && (
              <div className={quote.change_pct >= 0 ? "text-emerald-600" : "text-red-600"}>
                {quote.change_pct.toFixed(2)}%
              </div>
            )}
          </div>
          <div className="mt-1 flex items-center gap-2 text-xs text-slate-400">
            <span>source: {quote.source}</span>
            {connected && (
              <span className="flex items-center gap-1 text-emerald-600">
                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-500" />
                live
              </span>
            )}
            {liveQuote?.price && liveQuote.price !== quote.price && (
              <span className="text-amber-600">ws: {liveQuote.price.toFixed(2)}</span>
            )}
          </div>
        </Card>
      )}

      {bars && bars.bars.length > 0 && (
        <Card>
          <div className="mb-2 flex items-center justify-between">
            <h2 className="text-lg font-semibold">Price ({bars.timeframe})</h2>
            <div className="flex gap-1">
              {[10, 20, 50].map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => toggleSma(p)}
                  className={`rounded px-2 py-0.5 text-xs font-medium transition-colors ${
                    smaPeriods.includes(p)
                      ? "bg-brand/10 text-brand"
                      : "text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
                  }`}
                >
                  SMA {p}
                </button>
              ))}
              <button
                type="button"
                onClick={() => setShowRSI((v) => !v)}
                className={`rounded px-2 py-0.5 text-xs font-medium transition-colors ${
                  showRSI
                    ? "bg-brand/10 text-brand"
                    : "text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
                }`}
              >
                RSI
              </button>
              <button
                type="button"
                onClick={() => setShowMACD((v) => !v)}
                className={`rounded px-2 py-0.5 text-xs font-medium transition-colors ${
                  showMACD
                    ? "bg-brand/10 text-brand"
                    : "text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
                }`}
              >
                MACD
              </button>
            </div>
          </div>
          <PriceChart bars={bars.bars} smaPeriods={smaPeriods} />
          {showRSI && (
            <div className="mt-2 border-t border-slate-100 pt-2 dark:border-slate-800">
              <RSIPanel bars={bars.bars} />
            </div>
          )}
          {showMACD && (
            <div className="mt-2 border-t border-slate-100 pt-2 dark:border-slate-800">
              <MACDPanel bars={bars.bars} />
            </div>
          )}
        </Card>
      )}

      {bars && bars.bars.length > 0 && (
        <Card className="overflow-auto">
          <table className="w-full text-sm">
            <thead className="text-left text-slate-500">
              <tr>
                <th className="py-1">Date</th>
                <th className="py-1">Open</th>
                <th className="py-1">High</th>
                <th className="py-1">Low</th>
                <th className="py-1">Close</th>
                <th className="py-1">Volume</th>
              </tr>
            </thead>
            <tbody>
              {bars.bars.slice(-12).reverse().map((b) => (
                <tr key={b.ts} className="border-t border-slate-100 dark:border-slate-800">
                  <td className="py-1">{new Date(b.ts).toLocaleDateString()}</td>
                  <td className="py-1">{b.open.toFixed(2)}</td>
                  <td className="py-1">{b.high.toFixed(2)}</td>
                  <td className="py-1">{b.low.toFixed(2)}</td>
                  <td className="py-1">{b.close.toFixed(2)}</td>
                  <td className="py-1">{b.volume?.toLocaleString() ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
