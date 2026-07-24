import { cn } from "../../lib/cn";
import type { Bar } from "../../types/market";
import { computeMACD } from "../../lib/indicators";

interface Props {
  bars: Bar[];
  className?: string;
}

const VB_W = 800;
const VB_H = 120;
const PAD = { top: 8, right: 16, bottom: 20, left: 40 };

export function MACDPanel({ bars, className }: Props) {
  const { line, signal, hist } = computeMACD(bars);
  const allVals = [...line, ...signal].filter((v): v is number => v !== null);

  if (allVals.length < 2) {
    return (
      <div className={cn("flex h-20 items-center justify-center text-xs text-slate-400", className)}>
        Not enough data for MACD.
      </div>
    );
  }

  const innerW = VB_W - PAD.left - PAD.right;
  const innerH = VB_H - PAD.top - PAD.bottom;
  const n = line.length;

  let min = Math.min(...allVals, ...hist.filter((v): v is number => v !== null));
  let max = Math.max(...allVals, ...hist.filter((v): v is number => v !== null));
  if (min === max) { min -= 0.1; max += 0.1; }
  const span = max - min;
  min -= span * 0.1;
  max += span * 0.1;

  const x = (i: number) => PAD.left + (i / (n - 1)) * innerW;
  const y = (v: number) => PAD.top + (1 - (v - min) / (max - min)) * innerH;

  const toPath = (arr: (number | null)[]) =>
    arr
      .map((v, i) => (v !== null ? `${x(i).toFixed(1)},${y(v).toFixed(1)}` : null))
      .filter((p): p is string => p !== null)
      .map((p, i) => `${i === 0 ? "M" : "L"}${p}`)
      .join(" ");

  const barW = Math.max(1, (innerW / n) * 0.6);

  return (
    <svg
      role="img"
      aria-label="MACD"
      viewBox={`0 0 ${VB_W} ${VB_H}`}
      preserveAspectRatio="none"
      className={cn("h-24 w-full", className)}
    >
      <line
        x1={PAD.left}
        y1={y(0)}
        x2={VB_W - PAD.right}
        y2={y(0)}
        stroke="#cbd5e1"
        strokeWidth={0.5}
      />
      <text x={4} y={y(0)} dominantBaseline="middle" className="fill-slate-400 text-[10px]">
        0
      </text>

      {hist.map((v, i) =>
        v !== null ? (
          <rect
            key={i}
            x={x(i) - barW / 2}
            y={v >= 0 ? y(v) : y(0)}
            width={barW}
            height={Math.abs(y(v) - y(0))}
            fill={v >= 0 ? "#10b981" : "#ef4444"}
            fillOpacity={0.4}
          />
        ) : null,
      )}

      <path d={toPath(line)} fill="none" stroke="#3b82f6" strokeWidth={1.5} strokeLinejoin="round" />
      <path d={toPath(signal)} fill="none" stroke="#f59e0b" strokeWidth={1} strokeDasharray="3 2" />
    </svg>
  );
}
