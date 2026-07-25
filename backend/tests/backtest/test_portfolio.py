"""Tests for the portfolio backtester."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import numpy as np
import pandas as pd
import pytest

from app.backtest.portfolio_engine import _compute_weights, _run_portfolio, run_portfolio_backtest
from app.backtest.portfolio_schemas import PortfolioBacktestRequest
from app.marketdata.models import Bar, Bars

_BASE = datetime(2024, 1, 1, tzinfo=UTC)


def _fake_bars(symbol: str, n: int = 100, drift: float = 0.001) -> Bars:
    rng = np.random.default_rng(hash(symbol) % 2**32)
    close = 100 * np.exp(rng.standard_normal(n).cumsum() * 0.02 + drift)
    return Bars(
        symbol=symbol,
        timeframe="1d",
        source="test",
        bars=[
            Bar(
                ts=_BASE + timedelta(days=i),
                open=c,
                high=c + 1,
                low=c - 1,
                close=c,
                volume=1e6,
            )
            for i, c in enumerate(close)
        ],
    )


class TestComputeWeights:
    def test_equal_weight(self) -> None:
        req = PortfolioBacktestRequest(symbols=["A", "B", "C"])
        w = _compute_weights(req, ["A", "B", "C"])
        assert all(abs(v - 1 / 3) < 1e-10 for v in w.values())

    def test_custom_weights_normalized(self) -> None:
        req = PortfolioBacktestRequest(symbols=["A", "B"], weights={"A": 3, "B": 1})
        w = _compute_weights(req, ["A", "B"])
        assert abs(w["A"] - 0.75) < 1e-10
        assert abs(w["B"] - 0.25) < 1e-10


class TestRunPortfolio:
    def test_equal_weight_returns_equity(self) -> None:
        closes = pd.DataFrame(
            {
                "A": np.linspace(100, 110, 60),
                "B": np.linspace(100, 105, 60),
            },
            index=pd.date_range("2024-01-01", periods=60),
        )
        weights = {"A": 0.5, "B": 0.5}
        equity, returns = _run_portfolio(closes, weights, 0.0)
        assert len(equity) == 60
        assert equity.iloc[0] == pytest.approx(1.0)
        assert equity.iloc[-1] > 1.0  # both went up


@pytest.mark.asyncio
async def test_run_portfolio_backtest_end_to_end() -> None:
    req = PortfolioBacktestRequest(
        symbols=["AAA", "BBB"],
        timeframe="1d",
        limit=100,
    )
    with patch(
        "app.backtest.portfolio_engine.market_service.get_bars",
        new=AsyncMock(side_effect=[_fake_bars("AAA"), _fake_bars("BBB")]),
    ):
        result = await run_portfolio_backtest(req)

    assert result.symbols == ["AAA", "BBB"]
    assert result.n_bars >= 50
    assert "AAA" in result.weights
    assert "BBB" in result.weights
    assert abs(sum(result.weights.values()) - 1.0) < 0.01
    assert len(result.equity) >= 50
    assert result.metrics.total_return != 0


@pytest.mark.asyncio
async def test_portfolio_custom_weights() -> None:
    req = PortfolioBacktestRequest(
        symbols=["AAA", "BBB"],
        weights={"AAA": 0.7, "BBB": 0.3},
    )
    with patch(
        "app.backtest.portfolio_engine.market_service.get_bars",
        new=AsyncMock(side_effect=[_fake_bars("AAA"), _fake_bars("BBB")]),
    ):
        result = await run_portfolio_backtest(req)
    assert abs(result.weights["AAA"] - 0.7) < 0.01
    assert abs(result.weights["BBB"] - 0.3) < 0.01
