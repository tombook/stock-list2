"""Schemas — validation rules for the backtest API surface."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.backtest.schemas import BacktestRequest, StrategyRef


def test_request_defaults_applied() -> None:
    req = BacktestRequest(symbol="AAPL", strategy=StrategyRef(name="buy_hold"))
    assert req.timeframe == "1d"
    assert req.limit == 252
    assert req.cost_bps == 0.0


def test_request_rejects_limit_below_minimum() -> None:
    with pytest.raises(ValidationError):
        BacktestRequest(symbol="AAPL", strategy=StrategyRef(name="buy_hold"), limit=10)


def test_request_rejects_limit_above_maximum() -> None:
    with pytest.raises(ValidationError):
        BacktestRequest(symbol="AAPL", strategy=StrategyRef(name="buy_hold"), limit=5000)


def test_request_rejects_negative_cost() -> None:
    with pytest.raises(ValidationError):
        BacktestRequest(
            symbol="AAPL", strategy=StrategyRef(name="buy_hold"), cost_bps=-1.0
        )


def test_strategy_ref_accepts_arbitrary_params_dict() -> None:
    ref = StrategyRef(name="sma_cross", params={"fast": 5, "slow": 20})
    assert ref.params == {"fast": 5, "slow": 20}
