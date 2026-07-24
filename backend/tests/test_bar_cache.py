"""Tests for the bars_cache PG persistence layer."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.marketdata.bar_cache import cached_to_bars, fetch_cached, upsert_bars
from app.marketdata.models import Bar, Bars


def _make_bars(symbol: str = "TEST", n: int = 5) -> Bars:
    return Bars(
        symbol=symbol,
        timeframe="1d",
        source="test",
        bars=[
            Bar(
                ts=datetime(2024, 1, i + 1, tzinfo=UTC),
                open=100.0 + i,
                high=105.0 + i,
                low=95.0 + i,
                close=102.0 + i,
                volume=1_000_000.0,
            )
            for i in range(n)
        ],
    )


@pytest.mark.asyncio
async def test_upsert_then_fetch_round_trip(db_session: AsyncSession) -> None:
    bars = _make_bars("RDTP", 5)
    await upsert_bars(db_session, bars)

    rows = await fetch_cached(db_session, "RDTP", "1d", 5)
    assert rows is not None
    assert len(rows) == 5
    assert rows[0].close == 102.0
    assert rows[-1].close == 106.0


@pytest.mark.asyncio
async def test_fetch_returns_none_when_empty(db_session: AsyncSession) -> None:
    rows = await fetch_cached(db_session, "NOEXIST", "1d", 10)
    assert rows is None


@pytest.mark.asyncio
async def test_upsert_is_idempotent(db_session: AsyncSession) -> None:
    bars = _make_bars("IDEM", 3)
    await upsert_bars(db_session, bars)
    await upsert_bars(db_session, bars)  # ON CONFLICT DO NOTHING
    rows = await fetch_cached(db_session, "IDEM", "1d", 10)
    assert rows is not None
    assert len(rows) == 3


@pytest.mark.asyncio
async def test_cached_to_bars_preserves_data(db_session: AsyncSession) -> None:
    bars = _make_bars("CNVT", 2)
    await upsert_bars(db_session, bars)
    rows = await fetch_cached(db_session, "CNVT", "1d", 2)
    assert rows is not None
    result = cached_to_bars(rows, "CNVT", "1d")
    assert result.symbol == "CNVT"
    assert result.source == "cache"
    assert len(result.bars) == 2
    assert result.bars[0].close == 102.0


@pytest.mark.asyncio
async def test_fetch_respects_limit(db_session: AsyncSession) -> None:
    bars = _make_bars("LMT", 10)
    await upsert_bars(db_session, bars)
    rows = await fetch_cached(db_session, "LMT", "1d", 3)
    assert rows is not None
    assert len(rows) == 3
    # Should be the 3 most recent (highest ts)
    assert rows[-1].close == 111.0  # last bar
