import { create } from "zustand";
import { fetchAccount, fetchOrders, fetchPositions, placeOrder } from "../api/trading";
import type { Account, Order, Position, OrderRequest } from "../types/trading";

export interface TradingState {
  account: Account | null;
  orders: Order[];
  positions: Position[];
  loading: boolean;
  error: string | null;
  load: () => Promise<void>;
  submitOrder: (req: OrderRequest) => Promise<void>;
}

export const useTradingStore = create<TradingState>((set, get) => ({
  account: null,
  orders: [],
  positions: [],
  loading: false,
  error: null,

  load: async () => {
    set({ loading: true, error: null });
    try {
      const [account, orders, positions] = await Promise.all([
        fetchAccount(),
        fetchOrders(),
        fetchPositions(),
      ]);
      set({ account, orders, positions, loading: false });
    } catch (e) {
      set({ loading: false, error: e instanceof Error ? e.message : String(e) });
    }
  },

  submitOrder: async (req) => {
    try {
      await placeOrder(req);
      await get().load();
    } catch (e) {
      set({ error: e instanceof Error ? e.message : String(e) });
    }
  },
}));
