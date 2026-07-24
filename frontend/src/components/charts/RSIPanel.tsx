import { cn } from "../../lib/cn";
import type { Bar } from "../../types/market";
import { computeRSI } from "../../lib/indicators";

interface Props {
  bars: Bar[];
  length?: number;
  className?: string;
}

const VB_W = 800;
const VB_H = 120;
const PAD = { top: 8, right: 16, bottom: 20, left: 40 };

export function RSIPanel({ bars, length = 14, className }: Props) {
  const rsi = computeRSI(bars, length);
  const valid = rsi.filter((v): v is number => v !== null);

  if (valid.length < 2) {
    return (
      <div className={cn("flex h-20 items-center justify-center text-xs text-slate-400", className)}>
        Not enough data for RSI.
      </div>
    );
  }

  const innerW = VB_W - PAD.left - PAD.right;
  const innerH = VB_H - PAD.top - PAD.bottom;
  const n = rsi.length;

  const x = (i: number) => PAD.left + (i / (n - 1)) * innerW;
  const y = (v: number) => PAD.top + (1 - (v - 0) / 100) * innerH;

  const points = rsi
    .map((v, i) => (v !== null ? `${x(i).toFixed(1)},${y(v).toFixed(1)}` : null))
    .filter((p): p is string => p !== null);
  const linePath = points.map((p, i) => `${i === 0 ? "M" : "L"}${p}`).join(" ");

  const lastVal = valid[valid.length - 1];
  const color = lastVal > 70 ? "#ef4444" : lastVal < 30 ? "#10b981" : "#6366f1";

  return (
    <svg
      role="img"
      aria-label={`RSI(${length})`}
      viewBox={`0 0 ${VB_W} ${VB_H}`}
      preserveAspectRatio="none"
      className={cn("h-24 w-full", className)}
    >
      {[30, 50, 70].map((lvl) => (
        <g key={lvl}>
          <line
            x1={PAD.left}
            y1={y(lvl)}
            x2={VB_W - PAD.right}
            y2={y(lvl)}
            stroke={lvl === 50 ? "#cbd5e1" : "#f59e0b"}
            strokeWidth={0.5}
            strokeDasharray={lvl === 50 ? "" : "3 3"}
            opacity={0.5}
          />
          <text x={4} y={y(lvl)} dominantBaseline="middle" className="fill-slate-400 text-[10px]">
            {lvl}
          </text>
        </g>
      ))}
      <path d={linePath} fill="none" stroke={color} strokeWidth={1.5} strokeLinejoin="round" />
    </svg>
  );
}
