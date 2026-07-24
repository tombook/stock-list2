import { request } from "./client";
import type { RunSummary, RunDetail } from "../types/run";

/** GET /api/runs — 回测历史列表。 */
export function fetchRuns(): Promise<RunSummary[]> {
  return request<RunSummary[]>("/api/runs");
}

/** GET /api/runs/:id — 单条 run 完整详情（含 equity 曲线）。 */
export function fetchRun(id: number): Promise<RunDetail> {
  return request<RunDetail>(`/api/runs/${id}`);
}
