"""Tests for the indicator screener."""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pandas as pd
import pytest

from app.indicators.screener import ScanCondition, ScanRequest, _check_condition, run_scan
from app.marketdata.models import Bar, Bars

_BASE = datetime(2024, 1, 1, tzinfo=UTC)


def _make_bars(closes: list[float] | None = None) -> Bars:
    if closes is None:
        closes = [100 + 10 * math.sin(i / 8) + i * 0.3 for i in range(100)]
    return Bars(
        symbol="TEST",
        timeframe="1d",
        source="test",
        bars=[
            Bar(
                ts=_BASE + timedelta(days=i),
                open=c,
                high=c + 2,
                low=c - 2,
                close=c,
                volume=1e6,
            )
            for i, c in enumerate(closes)
        ],
    )


class TestCheckCondition:
    def test_lt(self) -> None:
        s = pd.Series([40, 35, 25])
        assert _check_condition(s, "lt", 30)

    def test_gt(self) -> None:
        s = pd.Series([10, 20, 35])
        assert _check_condition(s, "gt", 30)

    def test_cross_up(self) -> None:
        s = pd.Series([-1, 0, 1])
        assert _check_condition(s, "cross_up", None)

    def test_cross_down(self) -> None:
        s = pd.Series([1, 0, -1])
        assert _check_condition(s, "cross_down", None)


@pytest.mark.asyncio
async def test_run_scan_returns_matching_symbols() -> None:
    req = ScanRequest(
        symbols=["AAA", "BBB"],
        conditions=[ScanCondition(indicator="rsi", op="gt", value=50)],
    )
    bars = _make_bars()
    with patch(
        "app.indicators.screener.market_service.get_bars",
        new=AsyncMock(return_value=bars),
    ):
        result = await run_scan(req)
    assert result.total_checked == 2
    assert result.matched_count == 2
    assert all(m.symbol in {"AAA", "BBB"} for m in result.matched)


@pytest.mark.asyncio
async def test_run_scan_invalid_op_raises() -> None:
    req = ScanRequest(
        symbols=["X"],
        conditions=[ScanCondition(indicator="rsi", op="invalid", value=30)],
    )
    with pytest.raises(Exception, match="invalid operator"):
        await run_scan(req)
