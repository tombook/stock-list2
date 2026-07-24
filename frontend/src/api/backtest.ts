import { request } from "./client";
import type { BacktestRequest, BacktestResponse } from "../types/backtest";

/**
 * 调用 POST /api/backtest。
 * 回测需先拉取行情再向量计算，可能耗时较长，故给 60s 超时（client 默认仅 15s）。
 */
export function runBacktest(req: BacktestRequest): Promise<BacktestResponse> {
  return request<BacktestResponse>("/api/backtest", {
    method: "POST",
    body: req,
    timeoutMs: 60_000,
  });
}
