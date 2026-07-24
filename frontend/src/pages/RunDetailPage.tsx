import { useEffect } from "react";
import { Link, useParams } from "react-router-dom";
import { useRunsStore } from "../stores/runsStore";
import { Card } from "../components/ui/Card";
import { EquityChart } from "../components/charts/EquityChart";

function pct(v: number): string {
  return `${v >= 0 ? "+" : ""}${(v * 100).toFixed(2)}%`;
}
function num(v: number): string {
  return v.toFixed(2);
}

function MetricCard({ label, value, tone }: { label: string; value: string; tone?: "pos" | "neg" | "neutral" }) {
  const color =
    tone === "pos" ? "text-emerald-600" : tone === "neg" ? "text-red-600" : "text-slate-700 dark:text-slate-200";
  return (
    <div className="rounded-md border border-slate-200 p-3 dark:border-slate-800">
      <div className="text-xs text-slate-500">{label}</div>
      <div className={`mt-1 text-xl font-semibold ${color}`}>{value}</div>
    </div>
  );
}

export function RunDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { detail, detailLoading, detailError, loadDetail } = useRunsStore();

  useEffect(() => {
    const runId = Number(id);
    if (Number.isFinite(runId)) void loadDetail(runId);
  }, [id, loadDetail]);

  if (detailLoading && !detail) {
    return (
      <div className="mx-auto max-w-4xl">
        <Card className="text-center text-slate-400">Loading run…</Card>
      </div>
    );
  }

  if (detailError) {
    return (
      <div className="mx-auto max-w-4xl space-y-4">
        <Link to="/runs" className="text-sm text-brand hover:underline">
          ← Back to runs
        </Link>
        <Card className="border-red-300 text-red-600">{detailError}</Card>
      </div>
    );
  }

  if (!detail) return null;

  return (
    <div className="mx-auto max-w-4xl space-y-4">
      <Link to="/runs" className="text-sm text-brand hover:underline">
        ← Back to runs
      </Link>

      <Card>
        <div className="mb-3 flex items-baseline justify-between">
          <h2 className="text-lg font-semibold">
            {detail.symbol} · {detail.strategy_name}
          </h2>
          <span className="text-xs text-slate-400">
            {new Date(detail.period_start).toLocaleDateString()} → {new Date(detail.period_end).toLocaleDateString()} ·{" "}
            {detail.n_bars} bars
          </span>
        </div>

        <div className="mb-3 flex flex-wrap gap-4 text-xs text-slate-500">
          <span>params: {JSON.stringify(detail.strategy_params)}</span>
          <span>cost: {detail.cost_bps} bps</span>
          <span>timeframe: {detail.timeframe}</span>
          <span>created: {new Date(detail.created_at).toLocaleString()}</span>
        </div>

        <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
          <MetricCard label="Total Return" value={pct(detail.total_return)} tone={detail.total_return >= 0 ? "pos" : "neg"} />
          <MetricCard label="CAGR" value={pct(detail.cagr)} tone={detail.cagr >= 0 ? "pos" : "neg"} />
          <MetricCard label="Sharpe" value={num(detail.sharpe)} tone="neutral" />
          <MetricCard label="Max Drawdown" value={pct(detail.max_drawdown)} tone="neg" />
          <MetricCard label="Win Rate" value={pct(detail.win_rate)} tone="neutral" />
          <MetricCard label="Trades" value={String(detail.n_trades)} tone="neutral" />
        </div>
      </Card>

      <Card>
        <h2 className="mb-2 text-lg font-semibold">Equity Curve</h2>
        <EquityChart equity={detail.equity} />
      </Card>
    </div>
  );
}
