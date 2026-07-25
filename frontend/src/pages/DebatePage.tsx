/** Multi-agent debate visualization. Shows analyst opinions + PM synthesis. */

import { useState } from "react";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Input } from "../components/ui/Input";
import { request } from "../api/client";

type Signal = "bullish" | "bearish" | "neutral";

interface Opinion {
  signal: Signal;
  confidence: number;
  reasoning: string;
}

interface Conflict {
  high_divergence: boolean;
  bullish_count: number;
  bearish_count: number;
  neutral_count: number;
}

interface DebateResult {
  symbol: string;
  rounds: number;
  debate_log: { round: number; opinions: Record<string, Opinion> }[];
  final_opinions: Record<string, Opinion>;
  conflict: Conflict;
  risk_vetoed: boolean;
  fused_score: number;
  fused_label: Signal;
  portfolio_manager: { action: string; confidence: number; summary: string; key_factors: string[] };
  data_snapshot: Record<string, unknown>;
}

const SIGNAL_COLORS: Record<Signal, string> = {
  bullish: "text-emerald-600 bg-emerald-50 dark:bg-emerald-900/20",
  bearish: "text-red-600 bg-red-50 dark:bg-red-900/20",
  neutral: "text-slate-500 bg-slate-50 dark:bg-slate-800",
};

const ANALYST_LABELS: Record<string, string> = {
  technical: "Technical",
  fundamental: "Fundamental",
  sentiment: "Sentiment",
  news: "News",
  risk: "Risk",
};

export function DebatePage() {
  const [symbol, setSymbol] = useState("AAPL");
  const [result, setResult] = useState<DebateResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await request<DebateResult>("/api/analyze/debate", {
        method: "POST",
        body: { prompt: symbol, stream: false },
      });
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-4xl space-y-4">
      <h1 className="text-2xl font-bold">Multi-Agent Debate</h1>
      <p className="text-sm text-slate-500">
        5 specialist analysts independently assess the stock, then see each other's
        opinions and revise. The Portfolio Manager synthesizes the final recommendation
        with conflict detection and risk veto.
      </p>

      <form
        onSubmit={(e) => { e.preventDefault(); run(); }}
        className="flex flex-wrap items-end gap-3"
      >
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-slate-500">Symbol</span>
          <Input
            value={symbol}
            onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            placeholder="AAPL"
            className="w-32 uppercase"
          />
        </label>
        <Button type="submit" disabled={loading}>
          {loading ? "Running 2-round debate…" : "Start Debate"}
        </Button>
      </form>

      {error && <Card className="border-red-300 text-red-600">{error}</Card>}

      {result && (
        <>
          {/* PM synthesis card */}
          <Card className="border-2 border-brand/30">
            <div className="flex items-baseline justify-between">
              <h2 className="text-lg font-semibold">Portfolio Manager</h2>
              <span className={`text-2xl font-bold ${SIGNAL_COLORS[result.fused_label].split(" ")[0]}`}>
                {result.portfolio_manager.action.toUpperCase()}
              </span>
            </div>
            <p className="mt-2 text-sm text-slate-500">{result.portfolio_manager.summary}</p>
            <div className="mt-3 flex gap-4 text-xs text-slate-400">
              <span>Rounds: {result.rounds}</span>
              <span>Fused score: {result.fused_score.toFixed(2)} ({result.fused_label})</span>
              {result.risk_vetoed && <span className="text-red-600 font-semibold">⚠ Risk veto</span>}
              {result.conflict.high_divergence && (
                <span className="text-amber-600 font-semibold">⚠ High divergence</span>
              )}
            </div>
          </Card>

          {/* Final opinions grid */}
          <div>
            <h3 className="mb-2 text-sm font-semibold">Final Analyst Opinions</h3>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              {Object.entries(result.final_opinions).map(([domain, opinion]) => (
                <AnalystCard
                  key={domain}
                  label={ANALYST_LABELS[domain] || domain}
                  opinion={opinion}
                />
              ))}
            </div>
          </div>

          {/* Debate log (rounds) */}
          {result.debate_log.length > 1 && (
            <Card>
              <h3 className="mb-2 text-sm font-semibold">Debate Log ({result.debate_log.length} rounds)</h3>
              <div className="space-y-3 text-xs">
                {result.debate_log.map((round) => (
                  <div key={round.round}>
                    <div className="font-medium text-slate-500">Round {round.round}</div>
                    <div className="mt-1 grid grid-cols-5 gap-2">
                      {Object.entries(round.opinions).map(([domain, opinion]) => (
                        <div
                          key={domain}
                          className={`rounded p-1 ${SIGNAL_COLORS[opinion.signal]}`}
                        >
                          <div className="font-medium">{ANALYST_LABELS[domain] || domain}</div>
                          <div className="text-xs opacity-75">
                            {opinion.signal} ({opinion.confidence.toFixed(2)})
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </>
      )}
    </div>
  );
}

function AnalystCard({ label, opinion }: { label: string; opinion: Opinion }) {
  return (
    <Card className={`p-3 ${SIGNAL_COLORS[opinion.signal]}`}>
      <div className="flex items-baseline justify-between">
        <span className="text-sm font-medium">{label}</span>
        <span className="text-xs font-mono">
          {opinion.signal} · {(opinion.confidence * 100).toFixed(0)}%
        </span>
      </div>
      <p className="mt-1 text-xs leading-relaxed opacity-80">{opinion.reasoning}</p>
    </Card>
  );
}
