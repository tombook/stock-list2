import { type FormEvent, type ReactNode } from "react";
import { useBacktestStore } from "../stores/backtestStore";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { EquityChart } from "../components/charts/EquityChart";
import type { Metrics, StrategyName } from "../types/backtest";

/** 每个策略需要编辑的参数键及展示标签。 */
const STRATEGY_PARAMS: Record<StrategyName, { key: string; label: string }[]> = {
  sma_cross: [
    { key: "fast", label: "Fast" },
    { key: "slow", label: "Slow" },
  ],
  momentum: [{ key: "lookback", label: "Lookback" }],
  buy_hold: [],
};

const STRATEGIES: StrategyName[] = ["sma_cross", "momentum", "buy_hold"];
const TIMEFRAMES = ["1d", "1wk", "1mo"];

function pct(v: number): string {
  return `${v >= 0 ? "+" : ""}${(v * 100).toFixed(2)}%`;
}
function num(v: number): string {
  return v.toFixed(2);
}

function MetricCard({ label, value, tone }: { label: string; value: string; tone?: "pos" | "neg" | "neutral" }) {
  const color = tone === "pos" ? "text-emerald-600" : tone === "neg" ? "text-red-600" : "text-slate-700 dark:text-slate-200";
  return (
    <div className="rounded-md border border-slate-200 p-3 dark:border-slate-800">
      <div className="text-xs text-slate-500">{label}</div>
      <div className={`mt-1 text-xl font-semibold ${color}`}>{value}</div>
    </div>
  );
}

function metricsCards(m: Metrics): ReactNode {
  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
      <MetricCard label="Total Return" value={pct(m.total_return)} tone={m.total_return >= 0 ? "pos" : "neg"} />
      <MetricCard label="CAGR" value={pct(m.cagr)} tone={m.cagr >= 0 ? "pos" : "neg"} />
      <MetricCard label="Sharpe" value={num(m.sharpe)} tone="neutral" />
      <MetricCard label="Max Drawdown" value={pct(m.max_drawdown)} tone="neg" />
      <MetricCard label="Win Rate" value={pct(m.win_rate)} tone="neutral" />
      <MetricCard label="Trades" value={String(m.n_trades)} tone="neutral" />
    </div>
  );
}

const fieldClass = "rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand dark:border-slate-700 dark:bg-slate-900";

export function BacktestPage() {
  const {
    symbol,
    strategyName,
    params,
    timeframe,
    limit,
    costBps,
    result,
    loading,
    error,
    setSymbol,
    setStrategy,
    setParam,
    setTimeframe,
    setLimit,
    setCostBps,
    run,
  } = useBacktestStore();

  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (!loading) void run();
  };

  return (
    <div className="mx-auto max-w-4xl space-y-4">
      <h1 className="text-2xl font-bold">Backtest</h1>

      <Card>
        <form onSubmit={submit} className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <label className="col-span-1 flex flex-col gap-1 text-sm">
            <span className="text-slate-500">Symbol</span>
            <Input value={symbol} onChange={(e) => setSymbol(e.target.value.toUpperCase())} placeholder="AAPL" className="uppercase" />
          </label>

          <label className="col-span-1 flex flex-col gap-1 text-sm">
            <span className="text-slate-500">Strategy</span>
            <select
              className={fieldClass}
              value={strategyName}
              onChange={(e) => setStrategy(e.target.value as StrategyName)}
            >
              {STRATEGIES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </label>

          <label className="col-span-1 flex flex-col gap-1 text-sm">
            <span className="text-slate-500">Timeframe</span>
            <select className={fieldClass} value={timeframe} onChange={(e) => setTimeframe(e.target.value)}>
              {TIMEFRAMES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </label>

          <label className="col-span-1 flex flex-col gap-1 text-sm">
            <span className="text-slate-500">Bars</span>
            <Input
              type="number"
              min={50}
              max={1000}
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
            />
          </label>

          {STRATEGY_PARAMS[strategyName].map(({ key, label }) => (
            <label key={key} className="col-span-1 flex flex-col gap-1 text-sm">
              <span className="text-slate-500">{label}</span>
              <Input
                type="number"
                min={1}
                value={String(params[key] ?? "")}
                onChange={(e) => setParam(key, Number(e.target.value))}
              />
            </label>
          ))}

          <label className="col-span-1 flex flex-col gap-1 text-sm">
            <span className="text-slate-500">Cost (bps)</span>
            <Input
              type="number"
              min={0}
              value={costBps}
              onChange={(e) => setCostBps(Number(e.target.value))}
            />
          </label>

          <div className="col-span-2 flex items-end md:col-span-1">
            <Button type="submit" disabled={loading} className="w-full">
              {loading ? "Running…" : "Run"}
            </Button>
          </div>
        </form>
      </Card>

      {error && <Card className="border-red-300 text-red-600">{error}</Card>}

      {result && (
        <>
          <Card>
            <div className="mb-3 flex items-baseline justify-between">
              <h2 className="text-lg font-semibold">
                {result.symbol} · {result.strategy.name}
              </h2>
              <span className="text-xs text-slate-400">
                {new Date(result.start).toLocaleDateString()} → {new Date(result.end).toLocaleDateString()} · {result.n_bars} bars
              </span>
            </div>
            {metricsCards(result.metrics)}
          </Card>

          <Card>
            <div className="mb-2 flex items-baseline justify-between">
              <h2 className="text-lg font-semibold">Equity Curve</h2>
              {result.alpha !== null && result.alpha !== undefined && (
                <span className={`text-sm font-medium ${result.alpha >= 0 ? "text-emerald-600" : "text-red-600"}`}>
                  Alpha: {result.alpha >= 0 ? "+" : ""}{(result.alpha * 100).toFixed(2)}%
                </span>
              )}
            </div>
            <EquityChart equity={result.equity} benchmarkEquity={result.benchmark_equity} />
          </Card>
        </>
      )}
    </div>
  );
}
