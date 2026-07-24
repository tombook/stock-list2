import { cn } from "../../lib/cn";
import type { EquityPoint } from "../../types/backtest";
import {
  computeDrawdownPeriods,
  computeMonthlyReturns,
  computeReturnDistribution,
  computeRollingSharpe,
  computeUnderwater,
} from "../../lib/tearsheet";

interface Props {
  equity: EquityPoint[];
  className?: string;
}

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function pct(v: number): string {
  return `${v >= 0 ? "+" : ""}${v.toFixed(1)}%`;
}

function colorForReturn(r: number | null): string {
  if (r === null || Math.abs(r) < 0.01) return "bg-slate-100 dark:bg-slate-800";
  if (r > 5) return "bg-emerald-600 text-white";
  if (r > 2) return "bg-emerald-400 text-white";
  if (r > 0) return "bg-emerald-200 text-emerald-800";
  if (r > -2) return "bg-red-200 text-red-800";
  if (r > -5) return "bg-red-400 text-white";
  return "bg-red-600 text-white";
}

export function TearSheet({ equity, className }: Props) {
  if (equity.length < 14) {
    return (
      <div className={cn("py-4 text-center text-sm text-slate-400", className)}>
        Need at least 14 data points for tear sheet analysis.
      </div>
    );
  }

  const underwater = computeUnderwater(equity);
  const rollingSharpe = computeRollingSharpe(equity, 63);
  const monthly = computeMonthlyReturns(equity);
  const drawdowns = computeDrawdownPeriods(equity, 5);
  const dist = computeReturnDistribution(equity, 20);

  const years = [...new Set(monthly.map((m) => m.year))].sort();
  const wMin = Math.min(...underwater.map((d) => d.value));
  const wMax = 0;
  const sVals = rollingSharpe.map((d) => d.value).filter((v): v is number => v !== null);
  const sMin = sVals.length ? Math.min(...sVals) : -1;
  const sMax = sVals.length ? Math.max(...sVals) : 1;
  const dMax = Math.max(...dist.map((d) => d.count), 1);

  return (
    <div className={cn("space-y-4", className)}>
      <h3 className="text-lg font-semibold">Tear Sheet</h3>

      {/* Underwater plot */}
      <div>
        <h4 className="mb-1 text-sm font-medium text-slate-500">Underwater (Drawdown Depth)</h4>
        <svg viewBox="0 0 800 100" preserveAspectRatio="none" className="h-20 w-full">
          {(() => {
            const n = underwater.length;
            const x = (i: number) => 40 + (i / (n - 1)) * 744;
            const y = (v: number) => 8 + (1 - (v - wMin) / (wMax - wMin || 1)) * 72;
            const path = underwater
              .map((d, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(d.value).toFixed(1)}`)
              .join(" ");
            const areaPath = `${path} L${x(n - 1).toFixed(1)},80 L${x(0).toFixed(1)},80 Z`;
            return (
              <>
                <line x1={40} y1={y(0)} x2={784} y2={y(0)} stroke="#cbd5e1" strokeWidth={0.5} />
                <path d={areaPath} fill="#ef4444" fillOpacity={0.25} />
                <path d={path} fill="none" stroke="#ef4444" strokeWidth={1} />
              </>
            );
          })()}
        </svg>
      </div>

      {/* Rolling Sharpe */}
      <div>
        <h4 className="mb-1 text-sm font-medium text-slate-500">Rolling Sharpe (63-day)</h4>
        <svg viewBox="0 0 800 100" preserveAspectRatio="none" className="h-20 w-full">
          {(() => {
            const valid = rollingSharpe.filter((d) => d.value !== null) as {
              ts: string;
              value: number;
            }[];
            if (valid.length < 2) return null;
            const n = valid.length;
            const x = (i: number) => 40 + (i / (n - 1)) * 744;
            const y = (v: number) => 8 + (1 - (v - sMin) / (sMax - sMin || 1)) * 72;
            const path = valid
              .map((d, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(d.value).toFixed(1)}`)
              .join(" ");
            return (
              <>
                <line x1={40} y1={y(0)} x2={784} y2={y(0)} stroke="#cbd5e1" strokeWidth={0.5} strokeDasharray="2 2" />
                <path d={path} fill="none" stroke="#6366f1" strokeWidth={1.5} />
              </>
            );
          })()}
        </svg>
      </div>

      {/* Monthly returns heatmap */}
      <div>
        <h4 className="mb-1 text-sm font-medium text-slate-500">Monthly Returns</h4>
        <div className="overflow-x-auto">
          <table className="text-xs">
            <thead>
              <tr>
                <th className="px-1 py-0.5 text-slate-400">Year</th>
                {MONTHS.map((m) => (
                  <th key={m} className="px-1 py-0.5 text-slate-400">{m}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {years.map((year) => (
                <tr key={year}>
                  <td className="px-1 py-0.5 font-medium text-slate-500">{year}</td>
                  {MONTHS.map((_, monthIdx) => {
                    const cell = monthly.find((m) => m.year === year && m.month === monthIdx);
                    return (
                      <td key={monthIdx} className="p-0.5">
                        <div
                          className={`flex h-7 min-w-[2.5rem] items-center justify-center rounded text-[10px] ${colorForReturn(cell?.returnPct ?? null)}`}
                        >
                          {cell?.returnPct !== null && cell?.returnPct !== undefined
                            ? pct(cell.returnPct)
                            : ""}
                        </div>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Return distribution */}
      <div>
        <h4 className="mb-1 text-sm font-medium text-slate-500">Daily Return Distribution</h4>
        <svg viewBox="0 0 800 100" preserveAspectRatio="none" className="h-20 w-full">
          {dist.map((d, i) => {
            const barW = 744 / dist.length;
            const barH = (d.count / dMax) * 72;
            return (
              <rect
                key={i}
                x={40 + i * barW}
                y={80 - barH}
                width={barW * 0.85}
                height={barH}
                fill={d.binStart >= 0 ? "#10b981" : "#ef4444"}
                fillOpacity={0.6}
              />
            );
          })}
          <line x1={40} y1={80} x2={784} y2={80} stroke="#cbd5e1" strokeWidth={0.5} />
        </svg>
      </div>

      {/* Drawdown periods table */}
      <div>
        <h4 className="mb-1 text-sm font-medium text-slate-500">Worst Drawdown Periods</h4>
        <table className="w-full text-xs">
          <thead>
            <tr className="text-slate-400">
              <th className="py-1 text-left">#</th>
              <th className="py-1 text-left">Peak</th>
              <th className="py-1 text-left">Trough</th>
              <th className="py-1 text-right">Depth</th>
              <th className="py-1 text-right">Duration</th>
              <th className="py-1 text-left">Recovery</th>
            </tr>
          </thead>
          <tbody>
            {drawdowns.map((dd, i) => (
              <tr key={i} className="border-t border-slate-100 dark:border-slate-800">
                <td className="py-1">{i + 1}</td>
                <td className="py-1">{new Date(dd.peakDate).toLocaleDateString()}</td>
                <td className="py-1">{new Date(dd.troughDate).toLocaleDateString()}</td>
                <td className="py-1 text-right text-red-600">{dd.depth.toFixed(2)}%</td>
                <td className="py-1 text-right">{dd.duration} bars</td>
                <td className="py-1">
                  {dd.recoveryIdx !== null
                    ? new Date(equity[dd.recoveryIdx].ts).toLocaleDateString()
                    : "unrecovered"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
