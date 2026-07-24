/** 前端技术指标计算——从 Bar[] 数据计算常用指标值。
 *  镜像后端 app/indicators/ 的算法，用于 MarketsPage 副图面板。 */

import type { Bar } from "../types/market";

/** Wilder's RSI（与后端 momentum.rsi 一致）。 */
export function computeRSI(bars: Bar[], length = 14): (number | null)[] {
  const closes = bars.map((b) => b.close);
  const result: (number | null)[] = new Array(closes.length).fill(null);
  if (closes.length < length + 1) return result;

  let avgGain = 0;
  let avgLoss = 0;

  for (let i = 1; i <= length; i++) {
    const diff = closes[i] - closes[i - 1];
    if (diff > 0) avgGain += diff;
    else avgLoss -= diff;
  }
  avgGain /= length;
  avgLoss /= length;

  for (let i = length; i < closes.length; i++) {
    if (i > length) {
      const diff = closes[i] - closes[i - 1];
      const gain = diff > 0 ? diff : 0;
      const loss = diff < 0 ? -diff : 0;
      avgGain = (avgGain * (length - 1) + gain) / length;
      avgLoss = (avgLoss * (length - 1) + loss) / length;
    }
    const rs = avgLoss > 0 ? avgGain / avgLoss : 100;
    result[i] = avgLoss === 0 ? 100 : 100 - 100 / (1 + rs);
  }
  return result;
}

/** EMA（指数移动平均）。 */
function ema(values: number[], length: number): (number | null)[] {
  const result: (number | null)[] = new Array(values.length).fill(null);
  const k = 2 / (length + 1);
  let prev: number | null = null;

  for (let i = 0; i < values.length; i++) {
    if (i === length - 1) {
      const sum = values.slice(0, length).reduce((a, b) => a + b, 0);
      prev = sum / length;
      result[i] = prev;
    } else if (i >= length && prev !== null) {
      prev = values[i] * k + prev * (1 - k);
      result[i] = prev;
    }
  }
  return result;
}

/** MACD（线 + 信号 + 柱）。 */
export function computeMACD(
  bars: Bar[],
  fast = 12,
  slow = 26,
  signal = 9,
): { line: (number | null)[]; signal: (number | null)[]; hist: (number | null)[] } {
  const closes = bars.map((b) => b.close);
  const emaFast = ema(closes, fast);
  const emaSlow = ema(closes, slow);

  const line: (number | null)[] = closes.map((_, i) =>
    emaFast[i] !== null && emaSlow[i] !== null ? (emaFast[i]! - emaSlow[i]!) : null,
  );

  const lineValues = line.map((v) => v ?? 0);
  const signalResult = ema(lineValues, signal);

  const hist = line.map((v, i) =>
    v !== null && signalResult[i] !== null ? v - signalResult[i]! : null,
  );

  return { line, signal: signalResult, hist };
}
