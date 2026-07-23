export interface Quote {
  symbol: string;
  price: number;
  currency: string | null;
  name: string | null;
  change_pct: number | null;
  as_of: string | null;
  source: string;
}

export interface Bar {
  ts: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number | null;
}

export interface Bars {
  symbol: string;
  timeframe: string;
  bars: Bar[];
  source: string;
}

export interface DependencyStatus {
  status: string;
  detail: string | null;
}

export interface Health {
  status: string;
  version: string;
  dependencies: Record<string, DependencyStatus>;
}
