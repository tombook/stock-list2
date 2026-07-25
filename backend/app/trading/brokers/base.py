"""Broker protocol — unified interface for live trading.

Each broker implements: place_order, cancel_order, get_account, get_positions.
Adapters live in app/trading/brokers/.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class BrokerOrder:
    id: str
    symbol: str
    side: str
    qty: float
    status: str
    filled_price: float | None = None


@dataclass(frozen=True)
class BrokerPosition:
    symbol: str
    qty: float
    avg_cost: float


@dataclass(frozen=True)
class BrokerAccount:
    cash: float
    portfolio_value: float
    buying_power: float


class Broker(Protocol):
    name: str

    async def place_order(
        self,
        symbol: str,
        side: str,
        qty: float,
        order_type: str = "market",
        limit_price: float | None = None,
    ) -> BrokerOrder: ...

    async def cancel_order(self, order_id: str) -> None: ...

    async def get_account(self) -> BrokerAccount: ...

    async def get_positions(self) -> list[BrokerPosition]: ...

    async def stream_quotes(self, symbols: list[str]) -> AsyncIterator[dict]: ...
