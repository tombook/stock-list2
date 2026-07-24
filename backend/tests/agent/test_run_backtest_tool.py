"""run_backtest tool — service mocked; verifies the metrics-only payload."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.agent.tools import openai_tools, registry
from app.backtest.schemas import (
    BacktestResponse,
    EquityPoint,
    Metrics,
    StrategyRef,
)


def _ok_response() -> BacktestResponse:
    return BacktestResponse(
        symbol="AAPL",
        strategy=StrategyRef(name="sma_cross", params={"fast": 5, "slow": 20}),
        timeframe="1d",
        n_bars=252,
        start=datetime(2024, 1, 1),
        end=datetime(2024, 12, 30),
        metrics=Metrics(
            total_return=0.12,
            cagr=0.12,
            sharpe=0.9,
            max_drawdown=-0.18,
            win_rate=0.55,
            n_trades=6,
        ),
        equity=[EquityPoint(ts=datetime(2024, 1, 1), equity=1.0)],
    )


async def test_registry_exposes_run_backtest() -> None:
    assert "run_backtest" in registry()
    names = [t["function"]["name"] for t in openai_tools()]
    assert "run_backtest" in names


async def test_run_backtest_handler_returns_metrics_only() -> None:
    tool = registry()["run_backtest"]
    with patch(
        "app.agent.tools.run_backtest_service", new=AsyncMock(return_value=_ok_response())
    ):
        result = await tool.handler(
            {"symbol": "AAPL", "strategy": {"name": "sma_cross", "params": {"fast": 5, "slow": 20}}}
        )
    assert "equity" not in result  # equity stripped to save LLM tokens
    assert result["symbol"] == "AAPL"
    assert result["strategy"] == "sma_cross"
    assert result["total_return"] == 0.12
    assert result["sharpe"] == 0.9
    assert result["n_trades"] == 6


async def test_run_backtest_handler_applies_defaults() -> None:
    tool = registry()["run_backtest"]
    with patch(
        "app.agent.tools.run_backtest_service", new=AsyncMock(return_value=_ok_response())
    ) as m:
        await tool.handler({"symbol": "AAPL", "strategy": {"name": "buy_hold"}})
    sent = m.await_args.args[0]
    assert sent.timeframe == "1d"
    assert sent.limit == 252
    assert sent.cost_bps == 0.0


async def test_run_backtest_handler_propagates_errors_as_dict() -> None:
    from app.core.errors import NotFoundError

    tool = registry()["run_backtest"]
    with patch(
        "app.agent.tools.run_backtest_service",
        new=AsyncMock(side_effect=NotFoundError("unknown strategy: zzz")),
    ):
        with pytest.raises(NotFoundError):
            await tool.handler({"symbol": "AAPL", "strategy": {"name": "zzz"}})
