"""Backtest service — the only public async entry point.

Pulls bars via the market-data service, runs the vectorized engine in a worker
thread (pandas releases the GIL on most ops but we keep the event loop free),
and assembles the typed `BacktestResponse`.
"""

from __future__ import annotations

import asyncio

import pandas as pd

from app.backtest import engine, metrics
from app.backtest.schemas import (
    BacktestRequest,
    BacktestResponse,
    EquityPoint,
    Metrics,
)
from app.backtest.strategies import STRATEGIES
from app.core.errors import DomainError, NotFoundError
from app.marketdata import service as market_service
from app.marketdata.models import Bars


def _to_dataframe(bars: Bars) -> pd.DataFrame:
    rows = [
        {
            "ts": b.ts,
            "open": b.open,
            "high": b.high,
            "low": b.low,
            "close": b.close,
            "volume": b.volume,
        }
        for b in bars.bars
    ]
    return pd.DataFrame(rows)


def _run_sync(df: pd.DataFrame, req: BacktestRequest) -> engine.EngineResult:
    spec = STRATEGIES.get(req.strategy.name)
    if spec is None:
        raise NotFoundError(f"unknown strategy: {req.strategy.name}")
    try:
        signal = spec.fn(df, **req.strategy.params)
    except (ValueError, TypeError) as exc:
        raise DomainError(f"invalid strategy params: {exc}") from exc
    return engine.run(df, signal, cost_bps=req.cost_bps)


async def run_backtest(req: BacktestRequest) -> BacktestResponse:
    bars = await market_service.get_bars(req.symbol, req.timeframe, req.limit)
    df = _to_dataframe(bars)

    try:
        result = await asyncio.to_thread(_run_sync, df, req)
    except (DomainError, NotFoundError):
        raise
    except Exception as exc:  # engine blew up unexpectedly
        raise DomainError(f"backtest failed: {exc}") from exc

    ppy = metrics.periods_per_year(req.timeframe)
    rate, n_closed = metrics.win_rate(df, result.position)
    m = Metrics(
        total_return=metrics.total_return(result.equity),
        cagr=metrics.cagr(result.equity, ppy),
        sharpe=metrics.sharpe(result.strategy_returns, ppy),
        max_drawdown=metrics.max_drawdown(result.equity),
        win_rate=rate,
        n_trades=n_closed,
    )

    equity_points = [
        EquityPoint(ts=ts.to_pydatetime() if hasattr(ts, "to_pydatetime") else ts, equity=float(eq))
        for ts, eq in zip(df["ts"], result.equity, strict=True)
    ]

    return BacktestResponse(
        symbol=bars.symbol,
        strategy=req.strategy,
        timeframe=req.timeframe,
        n_bars=len(df),
        start=bars.bars[0].ts,
        end=bars.bars[-1].ts,
        metrics=m,
        equity=equity_points,
    )
