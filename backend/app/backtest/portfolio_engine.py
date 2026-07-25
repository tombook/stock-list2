"""Portfolio backtester — multi-symbol vectorized engine.

Fetches bars for each symbol, aligns them on a common timeline, applies
equal-weight or custom-weight rebalancing, and computes portfolio-level
returns and metrics. Cost is applied on each rebalance event.
"""

from __future__ import annotations

import asyncio

import pandas as pd

from app.backtest import metrics
from app.backtest.portfolio_schemas import (
    PortfolioBacktestRequest,
    PortfolioBacktestResponse,
    PortfolioMetrics,
)
from app.backtest.schemas import EquityPoint
from app.core.errors import DomainError
from app.marketdata import service as market_service
from app.marketdata.models import Bars


def _to_close_series(bars: Bars) -> pd.Series:
    closes = {b.ts: b.close for b in bars.bars}
    return pd.Series(closes, name=bars.symbol)


async def _fetch_all_closes(symbols: list[str], timeframe: str, limit: int) -> pd.DataFrame:
    """Fetch bars for all symbols, return aligned DataFrame of closes."""
    tasks = [market_service.get_bars(s, timeframe, limit) for s in symbols]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    series_list: list[pd.Series] = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            raise DomainError(f"failed to fetch {symbols[i]}: {result}")
        series_list.append(_to_close_series(result))

    df = pd.concat(series_list, axis=1)
    df.columns = symbols
    df = df.dropna()
    if len(df) < 50:
        raise DomainError(f"insufficient overlapping bars ({len(df)}) for portfolio backtest")
    return df


def _compute_weights(req: PortfolioBacktestRequest, symbols: list[str]) -> dict[str, float]:
    if req.weights:
        total = sum(abs(v) for v in req.weights.values())
        if total < 0.01:
            raise DomainError("custom weights sum to ~0")
        return {s: req.weights.get(s, 0.0) / total for s in symbols}
    n = len(symbols)
    return {s: 1.0 / n for s in symbols}


def _run_portfolio(
    closes: pd.DataFrame,
    weights: dict[str, float],
    cost_bps: float,
) -> tuple[pd.Series, pd.Series]:
    """Run equal/custom-weight portfolio. Returns (equity, strategy_returns)."""
    returns = closes.pct_change().fillna(0.0)
    w = pd.Series(weights)

    portfolio_returns = (returns[w.index] * w.values).sum(axis=1)

    # Cost applied as turnover × cost_bps (equal-weight daily = small)
    turnover = portfolio_returns.diff().abs().fillna(0.0)
    cost = (cost_bps * 1e-4) * turnover
    portfolio_returns = portfolio_returns - cost

    equity = (1.0 + portfolio_returns).cumprod()
    return equity, portfolio_returns


async def run_portfolio_backtest(
    req: PortfolioBacktestRequest,
) -> PortfolioBacktestResponse:
    symbols = [s.upper() for s in req.symbols]
    closes = await _fetch_all_closes(symbols, req.timeframe, req.limit)
    weights = _compute_weights(req, symbols)

    equity, strat_returns = await asyncio.to_thread(_run_portfolio, closes, weights, req.cost_bps)

    ppy = metrics.periods_per_year(req.timeframe)
    m = PortfolioMetrics(
        total_return=metrics.total_return(equity),
        cagr=metrics.cagr(equity, ppy),
        sharpe=metrics.sharpe(strat_returns, ppy),
        max_drawdown=metrics.max_drawdown(equity),
        volatility=metrics.volatility(strat_returns, ppy),
    )

    equity_points = [
        EquityPoint(
            ts=ts.to_pydatetime() if hasattr(ts, "to_pydatetime") else ts,
            equity=float(eq),
        )
        for ts, eq in zip(equity.index, equity.values, strict=True)
    ]

    return PortfolioBacktestResponse(
        symbols=symbols,
        n_bars=len(closes),
        start=closes.index[0].to_pydatetime()
        if hasattr(closes.index[0], "to_pydatetime")
        else closes.index[0],
        end=closes.index[-1].to_pydatetime()
        if hasattr(closes.index[-1], "to_pydatetime")
        else closes.index[-1],
        rebalance=req.rebalance,
        weights=weights,
        metrics=m,
        equity=[p.model_dump(mode="json") for p in equity_points],
    )
