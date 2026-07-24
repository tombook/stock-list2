"""Tests for the get_fundamentals agent tool."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.agent.tools import registry


@pytest.mark.asyncio
async def test_get_fundamentals_tool_calls_service_and_returns_dict() -> None:
    from app.marketdata.models import Fundamentals

    expected = Fundamentals(
        symbol="AAPL",
        name="Apple Inc",
        sector="Technology",
        industry="Consumer Electronics",
        market_cap=3e12,
        trailing_pe=30.5,
        forward_pe=28.0,
        price_to_book=45.0,
        dividend_yield=0.005,
        beta=1.2,
        fifty_two_week_high=220.0,
        fifty_two_week_low=150.0,
        source="yfinance",
    )
    with patch(
        "app.agent.tools.market_service.get_fundamentals",
        new=AsyncMock(return_value=expected),
    ):
        tool = registry()["get_fundamentals"]
        result = await tool.handler({"symbol": "AAPL"})

    assert result["symbol"] == "AAPL"
    assert result["sector"] == "Technology"
    assert result["trailing_pe"] == 30.5
    assert result["market_cap"] == 3e12


def test_get_fundamentals_in_openai_tools() -> None:
    from app.agent.tools import openai_tools

    names = [t["function"]["name"] for t in openai_tools()]
    assert "get_fundamentals" in names
