import { useEffect } from "react";
import { Link } from "react-router-dom";
import { useRunsStore } from "../stores/runsStore";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";

function pct(v: number): string {
  return `${v >= 0 ? "+" : ""}${(v * 100).toFixed(2)}%`;
}
function num(v: number): string {
  return v.toFixed(2);
}
function shortDate(iso: string): string {
  return new Date(iso).toLocaleDateString();
}

export function RunsPage() {
  const { list, listLoading, listError, loadList } = useRunsStore();

  useEffect(() => {
    if (!listLoading && list.length === 0 && !listError) {
      void loadList();
    }
  }, [list, listLoading, listError, loadList]);

  return (
    <div className="mx-auto max-w-4xl space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Run History</h1>
        <Button onClick={() => void loadList()} disabled={listLoading}>
          {listLoading ? "Loading…" : "Refresh"}
        </Button>
      </div>

      {listError && <Card className="border-red-300 text-red-600">{listError}</Card>}

      {listLoading && list.length === 0 && (
        <Card className="text-center text-slate-400">Loading runs…</Card>
      )}

      {!listLoading && list.length === 0 && !listError && (
        <Card className="text-center text-slate-400">No runs yet. Run a backtest to see history.</Card>
      )}

      {list.length > 0 && (
        <Card className="overflow-x-auto p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-xs text-slate-500 dark:border-slate-800">
                <th className="p-3">Symbol</th>
                <th className="p-3">Strategy</th>
                <th className="p-3 text-right">Return</th>
                <th className="p-3 text-right">Sharpe</th>
                <th className="p-3 text-right">MaxDD</th>
                <th className="p-3 text-right">Trades</th>
                <th className="p-3">Period</th>
                <th className="p-3">Date</th>
              </tr>
            </thead>
            <tbody>
              {list.map((r) => (
                <tr
                  key={r.id}
                  className="border-b border-slate-100 transition-colors last:border-0 hover:bg-slate-50 dark:border-slate-800/50 dark:hover:bg-slate-800/50"
                >
                  <td className="p-3">
                    <Link to={`/runs/${r.id}`} className="font-semibold text-brand hover:underline">
                      {r.symbol}
                    </Link>
                  </td>
                  <td className="p-3 text-slate-600 dark:text-slate-300">{r.strategy_name}</td>
                  <td className={`p-3 text-right font-medium ${r.total_return >= 0 ? "text-emerald-600" : "text-red-600"}`}>
                    {pct(r.total_return)}
                  </td>
                  <td className="p-3 text-right tabular-nums">{num(r.sharpe)}</td>
                  <td className="p-3 text-right text-red-600">{pct(r.max_drawdown)}</td>
                  <td className="p-3 text-right tabular-nums">{r.n_trades}</td>
                  <td className="p-3 text-xs text-slate-400">
                    {shortDate(r.period_start)} → {shortDate(r.period_end)}
                  </td>
                  <td className="p-3 text-xs text-slate-400">{shortDate(r.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
