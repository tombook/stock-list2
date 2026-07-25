"""Tests for chart pattern recognition service."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from app.chart_pattern.service import _bars_to_text, detect_patterns
from app.marketdata.models import Bar, Bars

_BASE = datetime(2024, 1, 1, tzinfo=UTC)


def _fake_bars(n: int = 30) -> Bars:
    bars = []
    price = 100.0
    for i in range(n):
        change = (i % 5 - 2) * 0.5
        o = price
        c = price + change
        h = max(o, c) + 1
        lo = min(o, c) - 1
        bars.append(
            Bar(
                ts=_BASE + timedelta(days=i),
                open=o,
                high=h,
                low=lo,
                close=c,
                volume=1_000_000.0,
            )
        )
        price = c
    return Bars(symbol="TEST", timeframe="1d", source="test", bars=bars)


class TestTextFormat:
    def test_bars_to_text_contains_headers(self) -> None:
        text = _bars_to_text(_fake_bars(10).bars)
        assert "Date" in text
        assert "Open" in text
        assert "Close" in text

    def test_bars_to_text_marks_up_down(self) -> None:
        text = _bars_to_text(_fake_bars(5).bars)
        assert "↑" in text or "↓" in text

    def test_bars_to_text_truncates(self) -> None:
        text = _bars_to_text(_fake_bars(100).bars, max_rows=10)
        assert "10 rows" not in text
        lines = [
            line
            for line in text.split("\n")
            if line
            and not line.startswith("-")
            and not line.startswith("Date")
            and not line.startswith("Summary")
        ]
        assert len(lines) <= 10

    def test_empty_bars(self) -> None:
        assert _bars_to_text([]) == "(no data)"


@pytest.mark.asyncio
async def test_detect_patterns_unconfigured_llm() -> None:
    with (
        patch(
            "app.chart_pattern.service.market_service.get_bars",
            new=AsyncMock(return_value=_fake_bars(30)),
        ),
        patch("app.chart_pattern.service.get_settings") as gs,
    ):
        gs.return_value.llm_base_url = ""
        result = await detect_patterns("TEST")

    assert result["source"] == "llm"
    assert result["patterns"] == []


@pytest.mark.asyncio
async def test_detect_patterns_parses_llm_response() -> None:
    fake_llm = {
        "patterns": [
            {
                "name": "double_bottom",
                "type": "bullish",
                "confidence": 0.8,
                "description": "W-shaped bottom at $95",
                "key_levels": [95.0, 105.0],
            }
        ],
        "summary": "Bullish double bottom formation",
    }

    with (
        patch(
            "app.chart_pattern.service.market_service.get_bars",
            new=AsyncMock(return_value=_fake_bars(30)),
        ),
        patch(
            "app.chart_pattern.service._call_llm",
            new=AsyncMock(return_value=fake_llm),
        ),
    ):
        result = await detect_patterns("AAPL")

    assert len(result["patterns"]) == 1
    assert result["patterns"][0]["name"] == "double_bottom"
    assert result["patterns"][0]["confidence"] == 0.8
