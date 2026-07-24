import { type FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useWatchlistStore } from "../stores/watchlistStore";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";

function shortDate(iso: string): string {
  return new Date(iso).toLocaleDateString();
}

export function WatchlistPage() {
  const { items, loading, error, load, add, remove } = useWatchlistStore();
  const [symbol, setSymbol] = useState("");
  const [note, setNote] = useState("");

  useEffect(() => {
    void load();
  }, [load]);

  const submit = (e: FormEvent) => {
    e.preventDefault();
    const sym = symbol.trim().toUpperCase();
    if (!sym) return;
    void add({ symbol: sym, note: note.trim() || null });
    setSymbol("");
    setNote("");
  };

  return (
    <div className="mx-auto max-w-4xl space-y-4">
      <h1 className="text-2xl font-bold">Watchlist</h1>

      <Card>
        <form onSubmit={submit} className="flex flex-wrap items-end gap-3">
          <label className="flex flex-col gap-1 text-sm">
            <span className="text-slate-500">Symbol</span>
            <Input
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              placeholder="AAPL"
              className="w-32 uppercase"
            />
          </label>
          <label className="flex flex-1 flex-col gap-1 text-sm">
            <span className="text-slate-500">Note (optional)</span>
            <Input value={note} onChange={(e) => setNote(e.target.value)} placeholder="bullish breakout" />
          </label>
          <Button type="submit">Add</Button>
        </form>
      </Card>

      {error && <Card className="border-red-300 text-red-600">{error}</Card>}

      {loading && items.length === 0 && (
        <Card className="text-center text-slate-400">Loading…</Card>
      )}

      {!loading && items.length === 0 && !error && (
        <Card className="text-center text-slate-400">Your watchlist is empty. Add a symbol above.</Card>
      )}

      {items.length > 0 && (
        <Card className="overflow-x-auto p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-xs text-slate-500 dark:border-slate-800">
                <th className="p-3">Symbol</th>
                <th className="p-3">Note</th>
                <th className="p-3">Added</th>
                <th className="p-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((it) => (
                <tr
                  key={it.id}
                  className="border-b border-slate-100 last:border-0 dark:border-slate-800/50"
                >
                  <td className="p-3">
                    <Link to={`/markets?symbol=${it.symbol}`} className="font-semibold text-brand hover:underline">
                      {it.symbol}
                    </Link>
                  </td>
                  <td className="p-3 text-slate-600 dark:text-slate-300">{it.note ?? "—"}</td>
                  <td className="p-3 text-xs text-slate-400">{shortDate(it.created_at)}</td>
                  <td className="p-3 text-right">
                    <button
                      onClick={() => void remove(it.id)}
                      className="rounded px-2 py-1 text-xs text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20"
                    >
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
