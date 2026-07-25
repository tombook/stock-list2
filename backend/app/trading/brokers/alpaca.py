"""Alpaca broker adapter — uses Alpaca's REST API for real trading.

Supports both paper (paper-api.alpaca.markets) and live (api.alpaca.markets)
trading. Active only when ALPACA_API_KEY + ALPACA_SECRET_KEY are configured.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.core.errors import UpstreamError
from app.core.logging import get_logger
from app.core.settings import get_settings
from app.trading.brokers.base import (
    BrokerAccount,
    BrokerOrder,
    BrokerPosition,
)

_log = get_logger(__name__)

_PAPER_BASE = "https://paper-api.alpaca.markets"
_LIVE_BASE = "https://api.alpaca.markets"


class AlpacaBroker:
    """Alpaca trading adapter. Uses paper trading by default; switch via settings."""

    name = "alpaca"

    def __init__(self) -> None:
        s = get_settings()
        if not s.alpaca_api_key or not s.alpaca_secret_key:
            raise UpstreamError("alpaca broker not configured (missing API keys)", 400)
        self._headers = {
            "APCA-API-KEY-ID": s.alpaca_api_key,
            "APCA-API-SECRET-KEY": s.alpaca_secret_key,
        }
        self._paper = True

    @property
    def _base(self) -> str:
        return _PAPER_BASE if self._paper else _LIVE_BASE

    async def _request(
        self, method: str, path: str, body: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.request(
                    method,
                    f"{self._base}{path}",
                    headers={
                        **self._headers,
                        "Content-Type": "application/json",
                    },
                    json=body,
                )
                if resp.status_code == 404:
                    return {"_status": 404}
                resp.raise_for_status()
                if not resp.text:
                    return {}
                return resp.json()
        except httpx.HTTPStatusError as exc:
            raise UpstreamError(
                f"alpaca {method} {path} failed: {exc.response.status_code}",
                502,
            ) from exc
        except Exception as exc:
            raise UpstreamError(f"alpaca request error: {exc}") from exc

    async def place_order(
        self,
        symbol: str,
        side: str,
        qty: float,
        order_type: str = "market",
        limit_price: float | None = None,
    ) -> BrokerOrder:
        body: dict[str, Any] = {
            "symbol": symbol.upper(),
            "side": side.lower(),
            "type": order_type.lower(),
            "qty": str(float(qty)),
            "time_in_force": "day",
        }
        if order_type == "limit" and limit_price is not None:
            body["limit_price"] = str(limit_price)

        data = await self._request("POST", "/v2/orders", body)
        return BrokerOrder(
            id=str(data.get("id", "")),
            symbol=data.get("symbol", symbol.upper()),
            side=data.get("side", side),
            qty=float(data.get("qty", qty)),
            status=data.get("status", "submitted"),
            filled_price=float(data["filled_avg_price"]) if data.get("filled_avg_price") else None,
        )

    async def cancel_order(self, order_id: str) -> None:
        await self._request("DELETE", f"/v2/orders/{order_id}")

    async def get_account(self) -> BrokerAccount:
        data = await self._request("GET", "/v2/account")
        return BrokerAccount(
            cash=float(data.get("cash", 0)),
            portfolio_value=float(data.get("portfolio_value", 0)),
            buying_power=float(data.get("buying_power", 0)),
        )

    async def get_positions(self) -> list[BrokerPosition]:
        data = await self._request("GET", "/v2/positions")
        if isinstance(data, dict):
            return []
        return [
            BrokerPosition(
                symbol=p["symbol"],
                qty=float(p["qty"]),
                avg_cost=float(p["avg_cost"]),
            )
            for p in data
        ]

    async def stream_quotes(self, symbols: list[str]) -> AsyncIterator[dict]:
        raise NotImplementedError("Alpaca WebSocket streaming requires tradeapi-stream; deferred")
