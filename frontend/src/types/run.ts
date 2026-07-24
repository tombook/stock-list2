/** 镜像 backend/app/runs/schemas.py 的 RunSummary / RunDetail。 */

import type { EquityPoint } from "./backtest";

/** 列表行——不含 equity 曲线和策略参数，轻量。 */
export interface RunSummary {
  id: number;
  symbol: string;
  strategy_name: string;
  timeframe: string;
  n_bars: number;
  period_start: string;
  period_end: string;
  total_return: number;
  sharpe: number;
  max_drawdown: number;
  n_trades: number;
  created_at: string;
}

/** 完整 run——含策略参数、全部指标和 equity 曲线，用于详情页。 */
export interface RunDetail extends RunSummary {
  strategy_params: Record<string, number | string>;
  cost_bps: number;
  cagr: number;
  win_rate: number;
  equity: EquityPoint[];
}
