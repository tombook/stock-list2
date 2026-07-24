"""Tests for the fundamentals data source and service layer."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.core.errors import NotFoundError
from app.marketdata.models import Fundamentals


@pytest.mark.asyncio
async def test_fundamentals_extracts_fields_from_info() -> None:
    from app.marketdata.sources import yfinance_src

    fake_info = {
        "longName": "Apple Inc",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "marketCap": 3000000000000,
        "trailingPE": 30.5,
        "forwardPE": 28.0,
        "priceToBook": 45.0,
        "dividendYield": 0.005,
        "beta": 1.2,
        "fiftyTwoWeekHigh": 220.0,
        "fiftyTwoWeekLow": 150.0,
    }
    with patch.object(yfinance_src.yfinance, "Ticker") as mock_ticker:
        mock_ticker.return_value.info = fake_info
        result = await yfinance_src.fundamentals("aapl")

    assert isinstance(result, Fundamentals)
    assert result.symbol == "AAPL"
    assert result.name == "Apple Inc"
    assert result.sector == "Technology"
    assert result.market_cap == 3e12
    assert result.trailing_pe == 30.5
    assert result.beta == 1.2


@pytest.mark.asyncio
async def test_fundamentals_handles_missing_fields_as_none() -> None:
    from app.marketdata.sources import yfinance_src

    with patch.object(yfinance_src.yfinance, "Ticker") as mock_ticker:
        mock_ticker.return_value.info = {"longName": "Small Co"}
        result = await yfinance_src.fundamentals("SMAL")

    assert result.name == "Small Co"
    assert result.sector is None
    assert result.market_cap is None
    assert result.trailing_pe is None


@pytest.mark.asyncio
async def test_fundamentals_raises_not_found_on_empty_info() -> None:
    from app.marketdata.sources import yfinance_src

    with patch.object(yfinance_src.yfinance, "Ticker") as mock_ticker:
        mock_ticker.return_value.info = {}
        with pytest.raises(NotFoundError):
            await yfinance_src.fundamentals("FAKE")


@pytest.mark.asyncio
async def test_service_caches_fundamentals() -> None:
    from app.marketdata import service

    service._fundamentals_cache.clear()
    call_count = 0

    async def mock_fund(symbol: str) -> Fundamentals:
        nonlocal call_count
        call_count += 1
        return Fundamentals(symbol=symbol, source="test")

    with patch.object(service.registry, "fundamentals", mock_fund):
        await service.get_fundamentals("AAPL")
        await service.get_fundamentals("AAPL")

    assert call_count == 1  # 第二次命中缓存
    service._fundamentals_cache.clear()
