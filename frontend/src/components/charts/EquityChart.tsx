import { useId } from "react";
import { cn } from "../../lib/cn";
import type { EquityPoint } from "../../types/backtest";

interface Props {
  equity: EquityPoint[];
  benchmarkEquity?: EquityPoint[] | null;
  className?: string;
}

const VB_W = 800;
const VB_H = 300;
const PAD = { top: 12, right: 16, bottom: 28, left: 56 };

function pct(v: number): string {
  // equity 从 1.0 起算；显示为相对起点累计收益率
  const r = (v - 1) * 100;
  return `${r >= 0 ? "+" : ""}${r.toFixed(1)}%`;
}

function shortDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "2-digit",
  });
}

/** 纯 SVG 权益曲线——折线 + 渐变填充 + 水平网格 + 坐标标签。跟随当前文本色，兼容 dark mode。 */
export function EquityChart({ equity, benchmarkEquity, className }: Props) {
  const gradId = useId();
  const n = equity.length;

  if (n < 2) {
    return (
      <div className={cn("flex h-48 items-center justify-center text-sm text-slate-400", className)}>
        Not enough data to chart.
      </div>
    );
  }

  const innerW = VB_W - PAD.left - PAD.right;
  const innerH = VB_H - PAD.top - PAD.bottom;

  const values = equity.map((p) => p.equity);
  if (benchmarkEquity) {
    values.push(...benchmarkEquity.map((p) => p.equity));
  }
  let min = Math.min(...values);
  let max = Math.max(...values);
  if (min === max) {
    min -= 0.01;
    max += 0.01;
  }
  // 上下各留 5% 视觉留白，避免折线贴边
  const span = max - min;
  min -= span * 0.05;
  max += span * 0.05;

  const x = (i: number) => PAD.left + (i / (n - 1)) * innerW;
  const y = (v: number) => PAD.top + (1 - (v - min) / (max - min)) * innerH;

  const linePath = equity.map((p, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(2)},${y(p.equity).toFixed(2)}`).join(" ");
  const areaPath = `${linePath} L${x(n - 1).toFixed(2)},${(PAD.top + innerH).toFixed(2)} L${x(0).toFixed(2)},${(PAD.top + innerH).toFixed(2)} Z`;

  // 四条水平网格线（含上下边界）
  const gridLines = [0, 1, 2, 3, 4].map((k) => {
    const gy = PAD.top + (k / 4) * innerH;
    const gv = max - (k / 4) * (max - min);
    return { gy, gv };
  });

  return (
    <svg
      role="img"
      aria-label="Equity curve"
      viewBox={`0 0 ${VB_W} ${VB_H}`}
      preserveAspectRatio="none"
      className={cn("h-64 w-full text-brand", className)}
    >
      <defs>
        <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="currentColor" stopOpacity="0.25" />
          <stop offset="100%" stopColor="currentColor" stopOpacity="0" />
        </linearGradient>
      </defs>

      {/* 水平网格 + Y 轴标签 */}
      {gridLines.map(({ gy, gv }, i) => (
        <g key={i}>
          <line
            x1={PAD.left}
            y1={gy}
            x2={VB_W - PAD.right}
            y2={gy}
            className="text-slate-200 dark:text-slate-700"
            stroke="currentColor"
            strokeWidth={1}
          />
          <text x={PAD.left - 8} y={gy} textAnchor="end" dominantBaseline="middle" className="fill-slate-400 text-[11px]">
            {pct(gv)}
          </text>
        </g>
      ))}

      {/* 区域填充 + 折线 */}
      <path d={areaPath} fill={`url(#${gradId})`} />
      <path d={linePath} fill="none" stroke="currentColor" strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />

      {/* Benchmark 对比线（虚线灰色） */}
      {benchmarkEquity && benchmarkEquity.length >= 2 && (() => {
        const bn = benchmarkEquity.length;
        const bx = (i: number) => PAD.left + (i / (bn - 1)) * innerW;
        const bPath = benchmarkEquity
          .map((p, i) => `${i === 0 ? "M" : "L"}${bx(i).toFixed(2)},${y(p.equity).toFixed(2)}`)
          .join(" ");
        return <path d={bPath} fill="none" stroke="#94a3b8" strokeWidth={1.5} strokeDasharray="4 3" opacity={0.8} />;
      })()}

      {/* Benchmark 图例 */}
      {benchmarkEquity && benchmarkEquity.length >= 2 && (
        <text x={VB_W - PAD.right} y={PAD.top + 4} textAnchor="end" className="fill-slate-400 text-[10px]">
          --- benchmark
        </text>
      )}

      {/* X 轴首尾日期标签 */}
      <text x={PAD.left} y={VB_H - 8} textAnchor="start" className="fill-slate-400 text-[11px]">
        {shortDate(equity[0].ts)}
      </text>
      <text x={VB_W - PAD.right} y={VB_H - 8} textAnchor="end" className="fill-slate-400 text-[11px]">
        {shortDate(equity[n - 1].ts)}
      </text>
    </svg>
  );
}
