"""Tests for the broker adapter layer."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.core.errors import UpstreamError
from app.trading.brokers import alpaca as alpaca_mod
from app.trading.brokers import get_broker


def _alpaca_broker():
    s = type(
        "S",
        (),
        {
            "alpaca_api_key": "test_key",
            "alpaca_secret_key": "test_secret",
        },
    )()
    with patch.object(alpaca_mod, "get_settings", return_value=s):
        return alpaca_mod.AlpacaBroker()


class TestBrokerFactory:
    def test_raises_when_unconfigured(self) -> None:
        s = type(
            "S",
            (),
            {
                "alpaca_api_key": "",
                "alpaca_secret_key": "",
            },
        )()
        import app.trading.brokers as brokers_mod

        with patch.object(brokers_mod, "_settings", return_value=s):
            with pytest.raises(UpstreamError, match="no broker configured"):
                get_broker()


class TestAlpacaBroker:
    @pytest.mark.asyncio
    async def test_place_order_parses_response(self) -> None:
        broker = _alpaca_broker()
        fake_resp = {
            "id": "abc123",
            "symbol": "AAPL",
            "side": "buy",
            "qty": "10.0",
            "status": "filled",
            "filled_avg_price": "150.25",
        }

        class FakeResp:
            status_code = 200
            text = '{"id": "abc123"}'

            def raise_for_status(self):
                pass

            def json(self):
                return fake_resp

        class FakeClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                pass

            async def request(self, method, url, **kw):
                return FakeResp()

        with patch.object(alpaca_mod.httpx, "AsyncClient", return_value=FakeClient()):
            order = await broker.place_order("AAPL", "buy", 10)

        assert order.id == "abc123"
        assert order.status == "filled"
        assert order.filled_price == 150.25

    @pytest.mark.asyncio
    async def test_cancel_order_returns_none(self) -> None:
        broker = _alpaca_broker()

        class FakeResp:
            status_code = 204
            text = ""

            def raise_for_status(self):
                pass

            def json(self):
                return {}

        class FakeClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                pass

            async def request(self, method, url, **kw):
                return FakeResp()

        with patch.object(alpaca_mod.httpx, "AsyncClient", return_value=FakeClient()):
            await broker.cancel_order("abc123")
