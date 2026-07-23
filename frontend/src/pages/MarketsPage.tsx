import { type FormEvent, useEffect, useState } from "react";
import { useMarketStore } from "../stores/marketStore";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";

export function MarketsPage() {
  const { symbol, quote, bars, loading, error, lookup } = useMarketStore();
  const [draft, setDraft] = useState(symbol);

  useEffect(() => {
    lookup(symbol);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (draft.trim()) lookup(draft.trim());
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
          <div className="mt-1 text-xs text-slate-400">source: {quote.source}</div>
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
