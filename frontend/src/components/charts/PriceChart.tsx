import { useId } from "react";
import { cn } from "../../lib/cn";
import type { Bar } from "../../types/market";

interface Props {
  bars: Bar[];
  /** 要叠加的 SMA 周期列表，如 [20, 50]。空数组 = 不叠加。 */
  smaPeriods?: number[];
  className?: string;
}

const VB_W = 800;
const VB_H = 360;
const PRICE_H = 260;
const PAD = { top: 12, right: 16, bottom: 28, left: 56 };
const VOL_H = 64;
const VOL_TOP = PAD.top + PRICE_H + 16;

// SMA 线颜色（周期越短越亮）
const SMA_COLORS: Record<number, string> = {
  5: "#f59e0b",
  10: "#f59e0b",
  20: "#3b82f6",
  50: "#8b5cf6",
  100: "#ec4899",
  200: "#6b7280",
};

function fmtPrice(v: number): string {
  return v.toFixed(v < 10 ? 2 : 0);
}

function shortDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "2-digit" });
}

/** 计算简单移动平均：前 period-1 个点为 null（数据不足）。 */
function computeSMA(bars: Bar[], period: number): (number | null)[] {
  const result: (number | null)[] = [];
  let sum = 0;
  for (let i = 0; i < bars.length; i++) {
    sum += bars[i].close;
    if (i >= period) sum -= bars[i - period].close;
    result.push(i >= period - 1 ? sum / period : null);
  }
  return result;
}

/** 纯 SVG 蜡烛图——OHLC 蜡烛 + 成交量柱 + 可选 SMA 叠加线。绿涨红跌，兼容 dark mode。 */
export function PriceChart({ bars, smaPeriods = [], className }: Props) {
  const gradId = useId();
  const n = bars.length;

  if (n < 2) {
    return (
      <div className={cn("flex h-48 items-center justify-center text-sm text-slate-400", className)}>
        Not enough data to chart.
      </div>
    );
  }

  const innerW = VB_W - PAD.left - PAD.right;

  // 价格范围（含 wick 极值）
  let pMin = Infinity;
  let pMax = -Infinity;
  let vMax = 0;
  for (const b of bars) {
    pMin = Math.min(pMin, b.low);
    pMax = Math.max(pMax, b.high);
    if (b.volume) vMax = Math.max(vMax, b.volume);
  }
  const pSpan = pMax - pMin || 1;
  pMin -= pSpan * 0.05;
  pMax += pSpan * 0.05;

  // 蜡烛宽度：最多占可用宽度的 80%，最少 1px
  const candleW = Math.max(1, Math.min((innerW / n) * 0.7, 12));
  const slot = innerW / n;

  const x = (i: number) => PAD.left + slot * (i + 0.5);
  const yPrice = (v: number) => PAD.top + (1 - (v - pMin) / (pMax - pMin)) * PRICE_H;
  const yVol = (v: number) => VOL_TOP + VOL_H - (vMax > 0 ? (v / vMax) * VOL_H : 0);

  // 四条水平网格线
  const gridLines = [0, 1, 2, 3, 4].map((k) => {
    const gy = PAD.top + (k / 4) * PRICE_H;
    const gv = pMax - (k / 4) * (pMax - pMin);
    return { gy, gv };
  });

  return (
    <svg
      role="img"
      aria-label="Price chart"
      viewBox={`0 0 ${VB_W} ${VB_H}`}
      preserveAspectRatio="none"
      className={cn("h-80 w-full", className)}
    >
      <defs>
        <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="currentColor" stopOpacity={0.08} />
          <stop offset="100%" stopColor="currentColor" stopOpacity={0} />
        </linearGradient>
      </defs>

      {/* 水平网格 + Y 轴价格标签 */}
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
            {fmtPrice(gv)}
          </text>
        </g>
      ))}

      {/* 成交量区底线 */}
      <line
        x1={PAD.left}
        y1={VOL_TOP + VOL_H}
        x2={VB_W - PAD.right}
        y2={VOL_TOP + VOL_H}
        className="text-slate-200 dark:text-slate-700"
        stroke="currentColor"
        strokeWidth={1}
      />

      {/* 蜡烛 + 成交量柱 */}
      {bars.map((b, i) => {
        const up = b.close >= b.open;
        const color = up ? "#10b981" : "#ef4444"; // emerald-500 / red-500
        const cx = x(i);
        const bodyTop = yPrice(Math.max(b.open, b.close));
        const bodyBot = yPrice(Math.min(b.open, b.close));
        const bodyH = Math.max(1, bodyBot - bodyTop);
        return (
          <g key={i}>
            {/* wick: high-low 影线 */}
            <line x1={cx} y1={yPrice(b.high)} x2={cx} y2={yPrice(b.low)} stroke={color} strokeWidth={1} />
            {/* body: open-close 实体 */}
            <rect x={cx - candleW / 2} y={bodyTop} width={candleW} height={bodyH} fill={color} rx={0.5} />
            {/* volume bar */}
            {b.volume && vMax > 0 && (
              <rect x={cx - candleW / 2} y={yVol(b.volume)} width={candleW} height={VOL_TOP + VOL_H - yVol(b.volume)} fill={color} fillOpacity={0.35} />
            )}
          </g>
        );
      })}

      {/* SMA 叠加线 */}
      {smaPeriods.map((period) => {
        if (period >= n) return null;
        const sma = computeSMA(bars, period);
        const points = sma
          .map((v, i) => (v !== null ? `${x(i).toFixed(2)},${yPrice(v).toFixed(2)}` : null))
          .filter((p): p is string => p !== null);
        if (points.length < 2) return null;
        const color = SMA_COLORS[period] ?? "#3b82f6";
        return (
          <path
            key={`sma-${period}`}
            d={`M${points.join(" L")}`}
            fill="none"
            stroke={color}
            strokeWidth={1.5}
            strokeLinejoin="round"
            opacity={0.8}
          />
        );
      })}

      {/* X 轴首尾日期 */}
      <text x={PAD.left} y={VB_H - 8} textAnchor="start" className="fill-slate-400 text-[11px]">
        {shortDate(bars[0].ts)}
      </text>
      <text x={VB_W - PAD.right} y={VB_H - 8} textAnchor="end" className="fill-slate-400 text-[11px]">
        {shortDate(bars[n - 1].ts)}
      </text>
    </svg>
  );
}
