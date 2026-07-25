"""Tests for the Alpaca data source adapter."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.core.errors import NotFoundError
from app.marketdata.sources import alpaca_src


class TestClassify:
    def test_us_equity(self) -> None:
        assert alpaca_src.classify("AAPL") is not None

    def test_hk_returns_none(self) -> None:
        assert alpaca_src.classify("0700.HK") is None

    def test_crypto_returns_none(self) -> None:
        assert alpaca_src.classify("BTC-USD") is None


class TestQuote:
    @pytest.mark.asyncio
    async def test_quote_parses_alpaca_response(self) -> None:
        fake_response = {
            "quote": {
                "ap": 195.50,
                "bp": 195.48,
                "t": "2024-06-01T14:30:00Z",
            }
        }

        class FakeResp:
            status_code = 200

            def raise_for_status(self):
                pass

            def json(self):
                return fake_response

        class FakeClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                pass

            async def get(self, url, **kw):
                return FakeResp()

        with patch.object(alpaca_src.httpx, "AsyncClient", return_value=FakeClient()):
            result = await alpaca_src.quote("AAPL")

        assert result.symbol == "AAPL"
        assert result.price == 195.50
        assert result.source == "alpaca"

    @pytest.mark.asyncio
    async def test_quote_raises_not_found_on_404(self) -> None:
        class FakeResp:
            status_code = 404

            def raise_for_status(self):
                import httpx

                raise httpx.HTTPStatusError(
                    "not found",
                    request=None,
                    response=self,  # type: ignore[arg-type]
                )

            def json(self):
                return {}

        class FakeClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                pass

            async def get(self, url, **kw):
                return FakeResp()

        with patch.object(alpaca_src.httpx, "AsyncClient", return_value=FakeClient()):
            with pytest.raises(NotFoundError):
                await alpaca_src.quote("FAKE")


class TestBars:
    @pytest.mark.asyncio
    async def test_bars_parses_alpaca_response(self) -> None:
        fake_response = {
            "bars": [
                {
                    "t": "2024-06-01T14:30:00Z",
                    "o": 195.0,
                    "h": 196.0,
                    "l": 194.5,
                    "c": 195.5,
                    "v": 1000000,
                },
                {
                    "t": "2024-06-02T14:30:00Z",
                    "o": 195.5,
                    "h": 197.0,
                    "l": 195.0,
                    "c": 196.5,
                    "v": 1200000,
                },
            ]
        }

        class FakeResp:
            status_code = 200

            def raise_for_status(self):
                pass

            def json(self):
                return fake_response

        class FakeClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                pass

            async def get(self, url, **kw):
                return FakeResp()

        with patch.object(alpaca_src.httpx, "AsyncClient", return_value=FakeClient()):
            result = await alpaca_src.bars("AAPL", "1d", 10)

        assert result.symbol == "AAPL"
        assert len(result.bars) == 2
        assert result.bars[0].close == 195.5
        assert result.source == "alpaca"


class TestNotSupported:
    @pytest.mark.asyncio
    async def test_fundamentals_raises_not_found(self) -> None:
        with pytest.raises(NotFoundError):
            await alpaca_src.fundamentals("AAPL")

    @pytest.mark.asyncio
    async def test_actions_raises_not_found(self) -> None:
        with pytest.raises(NotFoundError):
            await alpaca_src.actions("AAPL")
