/** Tear Sheet 计算工具——从 equity 曲线提取回测分析数据。
 *  镜像 Pyfolio 的核心分析：rolling Sharpe、underwater、月度收益、回撤期、收益分布。 */

export interface EquityPoint {
  ts: string;
  equity: number;
}

export interface DrawdownPeriod {
  peakIdx: number;
  troughIdx: number;
  recoveryIdx: number | null;
  peakDate: string;
  troughDate: string;
  depth: number;
  duration: number;
}

/** 从 equity 曲线计算逐 bar 收益率。 */
export function computeReturns(equity: EquityPoint[]): number[] {
  return equity.slice(1).map((p, i) => p.equity / equity[i].equity - 1);
}

/** 滚动 Sharpe Ratio（年化）。 */
export function computeRollingSharpe(
  equity: EquityPoint[],
  window = 126,
  periodsPerYear = 252,
): { ts: string; value: number | null }[] {
  const returns = computeReturns(equity);
  const result: { ts: string; value: number | null }[] = [];
  for (let i = 0; i < returns.length; i++) {
    if (i < window - 1) {
      result.push({ ts: equity[i + 1].ts, value: null });
      continue;
    }
    const slice = returns.slice(i - window + 1, i + 1);
    const mean = slice.reduce((a, b) => a + b, 0) / slice.length;
    const std = Math.sqrt(
      slice.reduce((a, b) => a + (b - mean) ** 2, 0) / slice.length,
    );
    const sharpe = std > 1e-10 ? (mean / std) * Math.sqrt(periodsPerYear) : 0;
    result.push({ ts: equity[i + 1].ts, value: sharpe });
  }
  return result;
}

/** 水下曲线：每个时点相对历史峰值的回撤比例。 */
export function computeUnderwater(
  equity: EquityPoint[],
): { ts: string; value: number }[] {
  let peak = equity[0]?.equity ?? 1;
  return equity.map((p) => {
    peak = Math.max(peak, p.equity);
    return { ts: p.ts, value: (p.equity / peak - 1) * 100 };
  });
}

/** 月度收益率矩阵（年×月），返回复合收益率百分比。 */
export function computeMonthlyReturns(
  equity: EquityPoint[],
): { year: number; month: number; returnPct: number | null }[] {
  const monthly: Record<string, { firstEq: number; lastEq: number }> = {};
  for (const p of equity) {
    const d = new Date(p.ts);
    const key = `${d.getFullYear()}-${d.getMonth()}`;
    if (!monthly[key]) {
      monthly[key] = { firstEq: p.equity, lastEq: p.equity };
    }
    monthly[key].lastEq = p.equity;
  }
  return Object.entries(monthly).map(([key, v]) => {
    const [year, month] = key.split("-").map(Number);
    const ret = v.lastEq / v.firstEq - 1;
    return { year, month, returnPct: Math.abs(ret) < 1e-10 ? 0 : ret * 100 };
  });
}

/** Top N 回撤期。 */
export function computeDrawdownPeriods(
  equity: EquityPoint[],
  topN = 5,
): DrawdownPeriod[] {
  const periods: DrawdownPeriod[] = [];
  let peakIdx = 0;
  let troughIdx = 0;
  let inDrawdown = false;

  for (let i = 1; i < equity.length; i++) {
    if (equity[i].equity >= equity[peakIdx].equity) {
      if (inDrawdown) {
        const depth =
          (equity[troughIdx].equity / equity[peakIdx].equity - 1) * 100;
        if (depth < -0.01) {
          periods.push({
            peakIdx,
            troughIdx,
            recoveryIdx: i,
            peakDate: equity[peakIdx].ts,
            troughDate: equity[troughIdx].ts,
            depth,
            duration: i - peakIdx,
          });
        }
        inDrawdown = false;
      }
      peakIdx = i;
      troughIdx = i;
    } else if (equity[i].equity < equity[troughIdx].equity) {
      troughIdx = i;
      inDrawdown = true;
    }
  }

  if (inDrawdown) {
    const depth = (equity[troughIdx].equity / equity[peakIdx].equity - 1) * 100;
    periods.push({
      peakIdx,
      troughIdx,
      recoveryIdx: null,
      peakDate: equity[peakIdx].ts,
      troughDate: equity[troughIdx].ts,
      depth,
      duration: equity.length - 1 - peakIdx,
    });
  }

  return periods.sort((a, b) => a.depth - b.depth).slice(0, topN);
}

/** 日收益率直方图分桶。 */
export function computeReturnDistribution(
  equity: EquityPoint[],
  bins = 20,
): { binStart: number; binEnd: number; count: number }[] {
  const returns = computeReturns(equity);
  if (returns.length === 0) return [];
  const min = Math.min(...returns);
  const max = Math.max(...returns);
  const span = max - min || 0.01;
  const binSize = span / bins;
  const histogram = new Array(bins).fill(0).map((_, i) => ({
    binStart: (min + i * binSize) * 100,
    binEnd: (min + (i + 1) * binSize) * 100,
    count: 0,
  }));
  for (const r of returns) {
    const idx = Math.min(Math.floor((r - min) / binSize), bins - 1);
    histogram[idx].count++;
  }
  return histogram;
}
