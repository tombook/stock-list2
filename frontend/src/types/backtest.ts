/** 镜像 backend/app/backtest/schemas.py 的请求/响应模型。 */

/** 后端 StrategyParam = int | float | str；JS 中整数与浮点统一为 number。 */
export type StrategyParam = number | string;

/** 内置策略名（与后端 strategies.py 的 STRATEGIES 注册表一致）。 */
export type StrategyName = "sma_cross" | "momentum" | "buy_hold";

export interface StrategyRef {
  name: StrategyName;
  params: Record<string, StrategyParam>;
}

/** POST /api/backtest 请求体；字段约束对齐后端 schemas（extra=forbid）。 */
export interface BacktestRequest {
  symbol: string;
  strategy: StrategyRef;
  timeframe?: string;
  limit?: number;
  cost_bps?: number;
  benchmark?: string | null;
}

export interface Metrics {
  total_return: number;
  cagr: number;
  sharpe: number;
  max_drawdown: number;
  win_rate: number;
  n_trades: number;
}

export interface EquityPoint {
  ts: string;
  equity: number;
}

export interface BacktestResponse {
  symbol: string;
  strategy: StrategyRef;
  timeframe: string;
  n_bars: number;
  start: string;
  end: string;
  metrics: Metrics;
  equity: EquityPoint[];
  benchmark_equity?: EquityPoint[] | null;
  alpha?: number | null;
}
