"""Parameter optimizer — grid search over strategy parameters.

Fetches bars once, then runs the engine for every parameter combination.
Returns sorted results for heatmap visualization.
"""

from __future__ import annotations

import asyncio
import itertools

import pandas as pd

from app.backtest import engine, metrics
from app.backtest.schemas import OptimizeRequest, OptimizeResult, OptimizeRow
from app.backtest.service import _to_dataframe
from app.backtest.strategies import STRATEGIES
from app.core.errors import DomainError, NotFoundError
from app.marketdata import service as market_service


def _grid(params: list[dict[str, object]]) -> list[dict[str, object]]:
    """Expand param ranges into all combinations."""
    keys = [p["name"] for p in params]
    value_lists = [p["values"] for p in params]
    return [dict(zip(keys, combo, strict=True)) for combo in itertools.product(*value_lists)]


def _run_single(
    df: pd.DataFrame, strategy_fn: object, params: dict[str, object], cost_bps: float
) -> OptimizeRow:
    try:
        signal = strategy_fn(df, **params)  # type: ignore[call-arg]
    except (ValueError, TypeError):
        return OptimizeRow(
            params=dict(params), total_return=0, sharpe=0, max_drawdown=0, n_trades=0
        )
    result = engine.run(df, signal, cost_bps=cost_bps)
    ppy = 252
    rate, n_closed = metrics.win_rate(df, result.position)
    return OptimizeRow(
        params=dict(params),
        total_return=metrics.total_return(result.equity),
        sharpe=metrics.sharpe(result.strategy_returns, ppy),
        max_drawdown=metrics.max_drawdown(result.equity),
        n_trades=n_closed,
    )


async def run_optimize(req: OptimizeRequest) -> OptimizeResult:
    spec = STRATEGIES.get(req.strategy)
    if spec is None:
        raise NotFoundError(f"unknown strategy: {req.strategy}")

    bars = await market_service.get_bars(req.symbol, req.timeframe, req.limit)
    df = _to_dataframe(bars)

    combinations = _grid([{"name": p.name, "values": p.values} for p in req.param_ranges])

    if len(combinations) > 200:
        raise DomainError(f"too many combinations ({len(combinations)}), max 200")

    def _run_all() -> list[OptimizeRow]:
        return [_run_single(df, spec.fn, combo, req.cost_bps) for combo in combinations]

    rows = await asyncio.to_thread(_run_all)

    reverse = req.target_metric != "max_drawdown"
    rows.sort(key=lambda r: getattr(r, req.target_metric), reverse=reverse)

    return OptimizeResult(
        symbol=bars.symbol,
        strategy=req.strategy,
        target_metric=req.target_metric,
        rows=rows,
        best=rows[0] if rows else None,
    )
