"""Tests for the multi-agent analysis framework."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.agent.analysts.framework import _call_llm, _gather_data, analyze_deep
from app.marketdata.models import Quote


@pytest.mark.asyncio
async def test_gather_data_collects_all_sources() -> None:
    with (
        patch(
            "app.agent.analysts.framework.market_service.get_quote",
            new=AsyncMock(return_value=Quote(symbol="AAPL", price=150.0, source="test")),
        ),
        patch(
            "app.agent.analysts.framework.market_service.get_fundamentals",
            new=AsyncMock(side_effect=Exception("no data")),
        ),
        patch(
            "app.agent.analysts.framework.analyze_sentiment",
            new=AsyncMock(side_effect=Exception("no news")),
        ),
        patch(
            "app.agent.analysts.framework.analyze_risk",
            new=AsyncMock(side_effect=Exception("no bars")),
        ),
        patch(
            "app.agent.analysts.framework.predict_direction",
            new=AsyncMock(side_effect=Exception("no data")),
        ),
    ):
        data = await _gather_data("AAPL")

    assert data["symbol"] == "AAPL"
    assert data["quote"].price == 150.0
    assert "error" in data["fundamentals"]


@pytest.mark.asyncio
async def test_call_llm_returns_neutral_when_unconfigured() -> None:
    result = await _call_llm("test prompt", "{}")
    assert result["signal"] == "neutral"
    assert result["confidence"] == 0.0


@pytest.mark.asyncio
async def test_analyze_deep_returns_structure() -> None:
    with (
        patch(
            "app.agent.analysts.framework._gather_data",
            new=AsyncMock(return_value={"symbol": "AAPL", "quote": {"price": 150}}),
        ),
        patch(
            "app.agent.analysts.framework._call_llm",
            new=AsyncMock(
                return_value={"signal": "bullish", "confidence": 0.7, "reasoning": "test"}
            ),
        ),
    ):
        result = await analyze_deep("AAPL")

    assert result["symbol"] == "AAPL"
    assert "analysts" in result
    assert "portfolio_manager" in result
    assert set(result["analysts"].keys()) == {
        "technical",
        "fundamental",
        "sentiment",
        "news",
        "risk",
    }
    assert result["analysts"]["technical"]["signal"] == "bullish"
