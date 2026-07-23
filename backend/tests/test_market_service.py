"""Market-data service — verifies caching and that the registry is the only I/O path.

The registry is mocked so these are true unit tests (no network).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from app.marketdata import service
from app.marketdata.models import Bar, Bars, Quote


async def test_get_quote_caches_second_call() -> None:
    fake = Quote(symbol="AAPL", price=123.0, source="test")
    with patch("app.marketdata.registry.quote", new=AsyncMock(return_value=fake)) as m:
        first = await service.get_quote("aapl")  # lowercase on purpose: checks normalization
        second = await service.get_quote("AAPL")
    assert first.price == 123.0
    assert second is first  # cached object identity
    m.assert_awaited_once()


async def test_get_bars_caches_second_call() -> None:
    from datetime import datetime  # noqa: PLC0415 — local import keeps module top clean

    bars = Bars(
        symbol="AAPL",
        timeframe="1d",
        bars=[Bar(ts=datetime(2024, 1, 1), open=1, high=2, low=0.5, close=1.5, volume=10)],
        source="test",
    )
    with patch("app.marketdata.registry.bars", new=AsyncMock(return_value=bars)) as m:
        await service.get_bars("AAPL", "1d", 10)
        await service.get_bars("AAPL", "1d", 10)
    m.assert_awaited_once()


async def test_get_quote_propagates_not_found() -> None:
    from app.core.errors import NotFoundError

    with patch("app.marketdata.registry.quote", new=AsyncMock(side_effect=NotFoundError("x"))):
        try:
            await service.get_quote("NOPE")
        except NotFoundError:
            return
    raise AssertionError("expected NotFoundError")
