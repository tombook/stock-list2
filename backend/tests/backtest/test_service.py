"""Service — market service mocked; verifies the round-trip and error mapping."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from app.backtest.schemas import BacktestRequest, StrategyRef
from app.backtest.service import run_backtest
from app.core.errors import DomainError, NotFoundError
from app.marketdata.models import Bar, Bars


def _fake_bars(symbol: str, n: int = 30) -> Bars:
    # gentle uptrend so sma_cross eventually signals
    closes = [100.0 * (1.0 + 0.01 * i) for i in range(n)]
    return Bars(
        symbol=symbol,
        timeframe="1d",
        bars=[
            Bar(ts=datetime(2024, 1, 1) + timedelta(days=i), open=c, high=c, low=c, close=c, volume=1000.0)
            for i, c in enumerate(closes)
        ],
        source="test",
    )


async def test_run_backtest_happy_path_returns_metrics_and_equity() -> None:
    req = BacktestRequest(
        symbol="AAPL",
        strategy=StrategyRef(name="sma_cross", params={"fast": 3, "slow": 10}),
        timeframe="1d",
        limit=50,
    )
    with patch(
        "app.marketdata.service.get_bars",
        new=AsyncMock(return_value=_fake_bars("AAPL", n=50)),
    ):
        resp = await run_backtest(req)

    assert resp.symbol == "AAPL"
    assert resp.strategy.name == "sma_cross"
    assert resp.n_bars == 50
    assert len(resp.equity) == 50
    assert resp.metrics.n_trades >= 0
    assert -1.0 <= resp.metrics.max_drawdown <= 0.0  # drawdown is non-positive


async def test_run_backtest_unknown_strategy_raises_not_found() -> None:
    req = BacktestRequest(symbol="AAPL", strategy=StrategyRef(name="nope"))
    with (
        patch(
            "app.marketdata.service.get_bars",
            new=AsyncMock(return_value=_fake_bars("AAPL")),
        ),
        pytest.raises(NotFoundError),
    ):
        await run_backtest(req)


async def test_run_backtest_bad_params_raise_domain_error() -> None:
    req = BacktestRequest(
        symbol="AAPL",
        strategy=StrategyRef(name="sma_cross", params={"fast": 50, "slow": 5}),
    )
    with (
        patch(
            "app.marketdata.service.get_bars",
            new=AsyncMock(return_value=_fake_bars("AAPL")),
        ),
        pytest.raises(DomainError),
    ):
        await run_backtest(req)


async def test_run_backtest_applies_cost_bps() -> None:
    req_no_cost = BacktestRequest(
        symbol="AAPL", strategy=StrategyRef(name="buy_hold"), cost_bps=0.0, limit=50
    )
    req_cost = BacktestRequest(
        symbol="AAPL", strategy=StrategyRef(name="buy_hold"), cost_bps=100.0, limit=50
    )
    bars = _fake_bars("AAPL", n=50)
    with patch("app.marketdata.service.get_bars", new=AsyncMock(return_value=bars)):
        no_cost = await run_backtest(req_no_cost)
        with_cost = await run_backtest(req_cost)
    # buy_hold enters once at the start → cost reduces final equity by ~cost_bps*1e-4
    assert with_cost.metrics.total_return < no_cost.metrics.total_return
