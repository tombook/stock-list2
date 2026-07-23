import { request } from "./client";
import type { Health } from "../types/market";

export function getHealth(): Promise<Health> {
  return request<Health>("/health");
}
