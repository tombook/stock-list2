"""Tests for the paper trading engine."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.marketdata.models import Quote


def _fake_quote(symbol: str = "AAPL", price: float = 150.0) -> Quote:
    return Quote(symbol=symbol, price=price, source="test")


@pytest.mark.asyncio
async def test_get_account_creates_default(api_client: AsyncClient) -> None:
    resp = await api_client.get("/api/trading/account")
    assert resp.status_code == 200
    body = resp.json()
    assert body["cash"] == 100_000.0
    assert body["initial_cash"] == 100_000.0


@pytest.mark.asyncio
async def test_market_buy_fills_immediately(api_client: AsyncClient) -> None:
    with patch(
        "app.trading.service.market_service.get_quote",
        new=AsyncMock(return_value=_fake_quote("AAPL", 150.0)),
    ):
        resp = await api_client.post(
            "/api/trading/orders",
            json={"symbol": "AAPL", "side": "buy", "qty": 10, "order_type": "market"},
        )
    assert resp.status_code == 200
    order = resp.json()
    assert order["status"] == "filled"
    assert order["filled_price"] == 150.0

    resp = await api_client.get("/api/trading/account")
    assert resp.json()["cash"] == 100_000.0 - 1500.0


@pytest.mark.asyncio
async def test_sell_reduces_position(api_client: AsyncClient) -> None:
    with patch(
        "app.trading.service.market_service.get_quote",
        new=AsyncMock(return_value=_fake_quote("MSFT", 300.0)),
    ):
        await api_client.post(
            "/api/trading/orders",
            json={"symbol": "MSFT", "side": "buy", "qty": 20, "order_type": "market"},
        )
        resp = await api_client.post(
            "/api/trading/orders",
            json={"symbol": "MSFT", "side": "sell", "qty": 5, "order_type": "market"},
        )
    assert resp.status_code == 200
    assert resp.json()["status"] == "filled"

    resp = await api_client.get("/api/trading/positions")
    positions = resp.json()
    msft = next(p for p in positions if p["symbol"] == "MSFT")
    assert msft["qty"] == 15.0


@pytest.mark.asyncio
async def test_insufficient_cash_rejected(api_client: AsyncClient) -> None:
    with patch(
        "app.trading.service.market_service.get_quote",
        new=AsyncMock(return_value=_fake_quote("BRK.A", 500_000.0)),
    ):
        resp = await api_client.post(
            "/api/trading/orders",
            json={"symbol": "BRK.A", "side": "buy", "qty": 1, "order_type": "market"},
        )
    assert resp.status_code == 400
    assert (
        "insufficient" in resp.json()["detail"].lower()
        if "detail" in resp.json()
        else "insufficient" in resp.json().get("error", "").lower()
    )


@pytest.mark.asyncio
async def test_limit_order_stays_pending(api_client: AsyncClient) -> None:
    with patch(
        "app.trading.service.market_service.get_quote",
        new=AsyncMock(return_value=_fake_quote("AAPL", 150.0)),
    ):
        resp = await api_client.post(
            "/api/trading/orders",
            json={
                "symbol": "AAPL",
                "side": "buy",
                "qty": 10,
                "order_type": "limit",
                "limit_price": 100.0,
            },
        )
    assert resp.status_code == 200
    assert resp.json()["status"] == "pending"


@pytest.mark.asyncio
async def test_cancel_pending_order(api_client: AsyncClient) -> None:
    with patch(
        "app.trading.service.market_service.get_quote",
        new=AsyncMock(return_value=_fake_quote("AAPL", 150.0)),
    ):
        resp = await api_client.post(
            "/api/trading/orders",
            json={
                "symbol": "AAPL",
                "side": "buy",
                "qty": 10,
                "order_type": "limit",
                "limit_price": 100.0,
            },
        )
    order_id = resp.json()["id"]

    resp = await api_client.delete(f"/api/trading/orders/{order_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"
