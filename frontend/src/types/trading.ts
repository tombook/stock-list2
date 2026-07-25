/** 镜像 backend/app/trading/schemas.py */

export interface Account {
  id: number;
  cash: number;
  initial_cash: number;
  created_at: string;
}

export interface Order {
  id: number;
  symbol: string;
  side: string;
  qty: number;
  order_type: string;
  limit_price: number | null;
  stop_price: number | null;
  trail_amount: number | null;
  status: string;
  filled_price: number | null;
  filled_at: string | null;
  created_at: string;
}

export interface Position {
  id: number;
  symbol: string;
  qty: number;
  avg_cost: number;
  updated_at: string;
}

export interface OrderRequest {
  symbol: string;
  side: string;
  qty: number;
  order_type?: string;
  limit_price?: number | null;
  stop_price?: number | null;
  trail_amount?: number | null;
}
