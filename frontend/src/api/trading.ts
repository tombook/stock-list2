import { request } from "./client";
import type { Account, Order, Position, OrderRequest } from "../types/trading";

export function fetchAccount(): Promise<Account> {
  return request<Account>("/api/trading/account");
}

export function fetchOrders(): Promise<Order[]> {
  return request<Order[]>("/api/trading/orders");
}

export function fetchPositions(): Promise<Position[]> {
  return request<Position[]>("/api/trading/positions");
}

export function placeOrder(body: OrderRequest): Promise<Order> {
  return request<Order>("/api/trading/orders", { method: "POST", body });
}

export function cancelOrder(id: number): Promise<Order> {
  return request<Order>(`/api/trading/orders/${id}`, { method: "DELETE" });
}
