import { create } from "zustand";
import { runBacktest } from "../api/backtest";
import type { BacktestResponse, StrategyName, StrategyParam } from "../types/backtest";

/** 各策略的默认参数（对齐后端 strategies.py 的 default_params）。 */
const DEFAULT_PARAMS: Record<StrategyName, Record<string, StrategyParam>> = {
  sma_cross: { fast: 5, slow: 20 },
  momentum: { lookback: 20 },
  buy_hold: {},
};

export interface BacktestState {
  // 表单字段
  symbol: string;
  strategyName: StrategyName;
  params: Record<string, StrategyParam>;
  timeframe: string;
  limit: number;
  costBps: number;
  // 结果
  result: BacktestResponse | null;
  loading: boolean;
  error: string | null;
  // 动作
  setSymbol: (v: string) => void;
  setStrategy: (name: StrategyName) => void;
  setParam: (key: string, value: StrategyParam) => void;
  setTimeframe: (v: string) => void;
  setCostBps: (v: number) => void;
  setLimit: (v: number) => void;
  run: () => Promise<void>;
}

export const useBacktestStore = create<BacktestState>((set, get) => ({
  symbol: "AAPL",
  strategyName: "sma_cross",
  params: { ...DEFAULT_PARAMS.sma_cross },
  timeframe: "1d",
  limit: 252,
  costBps: 0,
  result: null,
  loading: false,
  error: null,

  setSymbol: (v) => set({ symbol: v }),
  // 切换策略时重置为该策略的默认参数，避免残留无效字段
  setStrategy: (name) => set({ strategyName: name, params: { ...DEFAULT_PARAMS[name] } }),
  setParam: (key, value) => set((s) => ({ params: { ...s.params, [key]: value } })),
  setTimeframe: (v) => set({ timeframe: v }),
  setCostBps: (v) => set({ costBps: v }),
  setLimit: (v) => set({ limit: v }),

  run: async () => {
    const { symbol, strategyName, params, timeframe, limit, costBps } = get();
    set({ loading: true, error: null });
    try {
      const result = await runBacktest({
        symbol,
        strategy: { name: strategyName, params },
        timeframe,
        limit,
        cost_bps: costBps,
      });
      set({ result, loading: false });
    } catch (e) {
      set({ loading: false, error: e instanceof Error ? e.message : String(e) });
    }
  },
}));
