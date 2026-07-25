/** Strategy editor — online Python code editor + execution. */

import { type FormEvent, useState } from "react";
import CodeMirror from "@uiw/react-codemirror";
import { python } from "@codemirror/lang-python";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { request } from "../api/client";

const DEFAULT_CODE = `import pandas as pd

def strategy(bars, **params):
    close = bars["close"]
    sma_20 = close.rolling(20).mean()
    return (close > sma_20).astype(float)
`;

interface EquityPoint {
  ts: string;
  equity: number;
}

interface ExecuteResponse {
  equity: EquityPoint[];
  n_bars: number;
  total_return: number;
  Sharpe: number;
  error: string | null;
}

interface ValidateResponse {
  valid: boolean;
  issues: { line: number; message: string }[];
}

export function StrategyEditorPage() {
  const [code, setCode] = useState(DEFAULT_CODE);
  const [symbol, setSymbol] = useState("AAPL");
  const [result, setResult] = useState<ExecuteResponse | null>(null);
  const [issues, setIssues] = useState<{ line: number; message: string }[]>([]);
  const [running, setRunning] = useState(false);

  const validate = async () => {
    const res = await request<ValidateResponse>("/api/strategies/validate", {
      method: "POST",
      body: { code },
    });
    setIssues(res.issues);
  };

  const run = async (e: FormEvent) => {
    e.preventDefault();
    setRunning(true);
    setResult(null);
    setIssues([]);
    try {
      const res = await request<ExecuteResponse>("/api/strategies/execute", {
        method: "POST",
        body: { code, symbol, limit: 120 },
      });
      setResult(res);
    } catch (e) {
      setResult({ equity: [], n_bars: 0, total_return: 0, Sharpe: 0, error: String(e) });
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="mx-auto max-w-5xl space-y-4">
      <h1 className="text-2xl font-bold">Strategy Editor</h1>
      <p className="text-sm text-slate-500">
        Write a Python function <code>strategy(bars, **params) → pd.Series[float]</code> that
        returns position sizes in [-1, +1]. The function runs in a sandboxed subprocess
        with a 10-second timeout.
      </p>

      <Card className="p-0 overflow-hidden">
        <CodeMirror
          value={code}
          height="280px"
          extensions={[python()]}
          theme="light"
          onChange={(value) => setCode(value)}
        />
      </Card>

      <form onSubmit={run} className="flex flex-wrap items-end gap-3">
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-slate-500">Symbol</span>
          <input
            value={symbol}
            onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            placeholder="AAPL"
            className="w-32 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm uppercase dark:border-slate-700 dark:bg-slate-900"
          />
        </label>
        <Button type="button" variant="ghost" onClick={validate}>Validate</Button>
        <Button type="submit" disabled={running}>
          {running ? "Running…" : "Run Backtest"}
        </Button>
      </form>

      {issues.length > 0 && (
        <Card className="border-red-300">
          <h3 className="mb-2 text-sm font-semibold text-red-600">Validation Issues</h3>
          <ul className="space-y-1 text-sm">
            {issues.map((issue, i) => (
              <li key={i} className="text-red-600">
                Line {issue.line}: {issue.message}
              </li>
            ))}
          </ul>
        </Card>
      )}

      {result && (
        <Card>
          {result.error ? (
            <div className="text-red-600">{result.error}</div>
          ) : (
            <>
              <div className="mb-3 flex gap-6">
                <Metric label="Bars" value={String(result.n_bars)} />
                <Metric label="Total Return" value={`${(result.total_return * 100).toFixed(2)}%`} />
                <Metric label="Sharpe" value={result.Sharpe.toFixed(3)} />
              </div>
              <h3 className="mb-2 text-sm font-semibold">Equity Curve</h3>
              <EquitySparkline data={result.equity} />
            </>
          )}
        </Card>
      )}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xs text-slate-500">{label}</div>
      <div className="text-xl font-semibold">{value}</div>
    </div>
  );
}

function EquitySparkline({ data }: { data: EquityPoint[] }) {
  if (data.length < 2) return <div className="text-slate-400">No equity data</div>;
  const W = 800;
  const H = 100;
  const PAD = 8;
  const closes = data.map((d) => d.equity);
  const min = Math.min(...closes);
  const max = Math.max(...closes);
  const span = max - min || 1;
  const x = (i: number) => PAD + (i / (data.length - 1)) * (W - 2 * PAD);
  const y = (v: number) => PAD + (1 - (v - min) / span) * (H - 2 * PAD);
  const path = data.map((d, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(d.equity).toFixed(1)}`).join(" ");
  return (
    <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" className="h-24 w-full">
      <path d={path} fill="none" stroke="currentColor" className="text-brand" strokeWidth={1.5} />
    </svg>
  );
}
