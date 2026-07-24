"""POST /api/backtest — service mocked; verifies HTTP shape and error codes."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.backtest.schemas import (
    BacktestResponse,
    EquityPoint,
    Metrics,
    StrategyRef,
)
from app.core.errors import DomainError, NotFoundError
from app.main import create_app


def _ok_response() -> BacktestResponse:
    return BacktestResponse(
        symbol="AAPL",
        strategy=StrategyRef(name="buy_hold"),
        timeframe="1d",
        n_bars=10,
        start=datetime(2024, 1, 1),
        end=datetime(2024, 1, 10),
        metrics=Metrics(
            total_return=0.1,
            cagr=0.1,
            sharpe=1.0,
            max_drawdown=-0.05,
            win_rate=1.0,
            n_trades=1,
        ),
        equity=[EquityPoint(ts=datetime(2024, 1, 1), equity=1.0)],
    )


async def test_backtest_happy_path_returns_200() -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    with patch(
        "app.api.backtest.run_backtest", new=AsyncMock(return_value=_ok_response())
    ):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post(
                "/api/backtest",
                json={"symbol": "AAPL", "strategy": {"name": "buy_hold"}},
            )
    assert resp.status_code == 200
    body = resp.json()
    assert body["symbol"] == "AAPL"
    assert body["metrics"]["total_return"] == 0.1


async def test_backtest_unknown_strategy_returns_404() -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    with patch(
        "app.api.backtest.run_backtest",
        new=AsyncMock(side_effect=NotFoundError("nope")),
    ):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post(
                "/api/backtest",
                json={"symbol": "AAPL", "strategy": {"name": "nope"}},
            )
    assert resp.status_code == 404


async def test_backtest_bad_params_return_400() -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    with patch(
        "app.api.backtest.run_backtest",
        new=AsyncMock(side_effect=DomainError("bad", 400)),
    ):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post(
                "/api/backtest",
                json={"symbol": "AAPL", "strategy": {"name": "buy_hold"}, "limit": 50},
            )
    assert resp.status_code == 400


async def test_backtest_validation_error_returns_422() -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/backtest", json={"strategy": {"name": "buy_hold"}})
    assert resp.status_code == 422  # missing required `symbol`
