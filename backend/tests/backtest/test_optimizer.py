"""Tests for the parameter optimizer (grid search)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from app.backtest.optimizer import _grid, run_optimize
from app.backtest.schemas import OptimizeRequest, ParamRange
from app.marketdata.models import Bar, Bars

_BASE = datetime(2024, 1, 1, tzinfo=UTC)


def _fake_bars(symbol: str = "TEST") -> Bars:
    return Bars(
        symbol=symbol,
        timeframe="1d",
        source="test",
        bars=[
            Bar(
                ts=_BASE + timedelta(days=i),
                open=100 + i,
                high=105 + i,
                low=95 + i,
                close=102 + i,
                volume=1e6,
            )
            for i in range(100)
        ],
    )


class TestGridExpansion:
    def test_two_params_cartesian_product(self) -> None:
        params = [
            {"name": "fast", "values": [5, 10]},
            {"name": "slow", "values": [20, 30, 40]},
        ]
        combos = _grid(params)
        assert len(combos) == 6
        assert {"fast": 5, "slow": 20} in combos
        assert {"fast": 10, "slow": 40} in combos

    def test_single_param(self) -> None:
        combos = _grid([{"name": "lookback", "values": [10, 20, 30]}])
        assert len(combos) == 3


@pytest.mark.asyncio
async def test_run_optimize_returns_sorted_rows() -> None:
    req = OptimizeRequest(
        symbol="TEST",
        strategy="sma_cross",
        param_ranges=[
            ParamRange(name="fast", values=[3, 5]),
            ParamRange(name="slow", values=[10, 20]),
        ],
        target_metric="sharpe",
    )
    with patch(
        "app.backtest.optimizer.market_service.get_bars",
        new=AsyncMock(return_value=_fake_bars()),
    ):
        result = await run_optimize(req)

    assert result.symbol == "TEST"
    assert result.strategy == "sma_cross"
    assert len(result.rows) == 4
    assert result.best is not None
    assert result.best.params in [
        {"fast": 3, "slow": 10},
        {"fast": 3, "slow": 20},
        {"fast": 5, "slow": 10},
        {"fast": 5, "slow": 20},
    ]
    sharpe_values = [r.sharpe for r in result.rows]
    assert sharpe_values == sorted(sharpe_values, reverse=True)


@pytest.mark.asyncio
async def test_run_optimize_unknown_strategy_raises() -> None:
    req = OptimizeRequest(
        symbol="TEST",
        strategy="nonexistent",
        param_ranges=[ParamRange(name="x", values=[1])],
    )
    with pytest.raises(Exception, match="unknown strategy"):
        await run_optimize(req)
