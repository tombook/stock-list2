import { type FormEvent, useEffect, useState } from "react";
import { useTradingStore } from "../stores/tradingStore";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";

export function TradingPage() {
  const { account, orders, positions, loading, error, load, submitOrder } =
    useTradingStore();
  const [symbol, setSymbol] = useState("");
  const [qty, setQty] = useState("1");
  const [side, setSide] = useState("buy");
  const [orderType, setOrderType] = useState("market");
  const [limitPrice, setLimitPrice] = useState("");

  useEffect(() => {
    void load();
  }, [load]);

  const submit = (e: FormEvent) => {
    e.preventDefault();
    const sym = symbol.trim().toUpperCase();
    if (!sym) return;
    void submitOrder({
      symbol: sym,
      side,
      qty: Number(qty),
      order_type: orderType,
      limit_price: orderType === "limit" || orderType === "stop_limit" ? Number(limitPrice) : null,
      stop_price: orderType === "stop" || orderType === "stop_limit" ? Number(limitPrice) : null,
    });
    setSymbol("");
    setLimitPrice("");
  };

  const totalValue =
    account?.cash ?? 0 +
    positions.reduce((sum, p) => sum + p.qty * p.avg_cost, 0);
  const pnl = totalValue - (account?.initial_cash ?? 100_000);

  return (
    <div className="mx-auto max-w-4xl space-y-4">
      <h1 className="text-2xl font-bold">Paper Trading</h1>

      {/* Account summary */}
      {account && (
        <Card>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <div className="text-xs text-slate-500">Cash</div>
              <div className="text-xl font-semibold">
                ${account.cash.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </div>
            </div>
            <div>
              <div className="text-xs text-slate-500">Portfolio Value</div>
              <div className="text-xl font-semibold">${totalValue.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
            </div>
            <div>
              <div className="text-xs text-slate-500">PnL</div>
              <div className={`text-xl font-semibold ${pnl >= 0 ? "text-emerald-600" : "text-red-600"}`}>
                {pnl >= 0 ? "+" : ""}${pnl.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Order form */}
      <Card>
        <form onSubmit={submit} className="flex flex-wrap items-end gap-3">
          <label className="flex flex-col gap-1 text-sm">
            <span className="text-slate-500">Symbol</span>
            <Input value={symbol} onChange={(e) => setSymbol(e.target.value.toUpperCase())} placeholder="AAPL" className="w-32 uppercase" />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            <span className="text-slate-500">Qty</span>
            <Input type="number" min={1} value={qty} onChange={(e) => setQty(e.target.value)} className="w-20" />
          </label>
          <select value={side} onChange={(e) => setSide(e.target.value)} className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm dark:border-slate-700 dark:bg-slate-900">
            <option value="buy">Buy</option>
            <option value="sell">Sell</option>
          </select>
          <select value={orderType} onChange={(e) => setOrderType(e.target.value)} className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm dark:border-slate-700 dark:bg-slate-900">
            <option value="market">Market</option>
            <option value="limit">Limit</option>
            <option value="stop">Stop</option>
            <option value="stop_limit">Stop Limit</option>
            <option value="trailing_stop">Trailing Stop</option>
          </select>
          {(orderType === "limit" || orderType === "stop" || orderType === "stop_limit") && (
            <label className="flex flex-col gap-1 text-sm">
              <span className="text-slate-500">Price</span>
              <Input type="number" value={limitPrice} onChange={(e) => setLimitPrice(e.target.value)} placeholder="0.00" className="w-24" />
            </label>
          )}
          <Button type="submit" disabled={loading}>{side === "buy" ? "Buy" : "Sell"}</Button>
        </form>
      </Card>

      {error && <Card className="border-red-300 text-red-600">{error}</Card>}

      {/* Positions */}
      {positions.length > 0 && (
        <Card className="overflow-x-auto p-0">
          <div className="p-3 text-sm font-semibold">Positions</div>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-xs text-slate-500 dark:border-slate-800">
                <th className="p-3">Symbol</th>
                <th className="p-3 text-right">Qty</th>
                <th className="p-3 text-right">Avg Cost</th>
                <th className="p-3 text-right">Value</th>
              </tr>
            </thead>
            <tbody>
              {positions.map((p) => (
                <tr key={p.id} className="border-b border-slate-100 last:border-0 dark:border-slate-800/50">
                  <td className="p-3 font-semibold">{p.symbol}</td>
                  <td className="p-3 text-right tabular-nums">{p.qty}</td>
                  <td className="p-3 text-right tabular-nums">${p.avg_cost.toFixed(2)}</td>
                  <td className="p-3 text-right tabular-nums">${(p.qty * p.avg_cost).toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      {/* Orders */}
      {orders.length > 0 && (
        <Card className="overflow-x-auto p-0">
          <div className="p-3 text-sm font-semibold">Order History</div>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-xs text-slate-500 dark:border-slate-800">
                <th className="p-3">Symbol</th>
                <th className="p-3">Side</th>
                <th className="p-3 text-right">Qty</th>
                <th className="p-3">Type</th>
                <th className="p-3">Status</th>
                <th className="p-3 text-right">Price</th>
              </tr>
            </thead>
            <tbody>
              {orders.slice(0, 20).map((o) => (
                <tr key={o.id} className="border-b border-slate-100 last:border-0 dark:border-slate-800/50">
                  <td className="p-3 font-semibold">{o.symbol}</td>
                  <td className={`p-3 ${o.side === "buy" ? "text-emerald-600" : "text-red-600"}`}>{o.side}</td>
                  <td className="p-3 text-right tabular-nums">{o.qty}</td>
                  <td className="p-3 text-xs text-slate-500">{o.order_type}</td>
                  <td className="p-3">
                    <span className={`rounded px-1.5 py-0.5 text-xs ${o.status === "filled" ? "bg-emerald-100 text-emerald-700" : o.status === "pending" ? "bg-amber-100 text-amber-700" : "bg-slate-100 text-slate-500"}`}>
                      {o.status}
                    </span>
                  </td>
                  <td className="p-3 text-right tabular-nums">{o.filled_price ? `$${o.filled_price.toFixed(2)}` : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
