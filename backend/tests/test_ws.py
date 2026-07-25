"""Tests for the WebSocket quote stream."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.marketdata.models import Quote
from app.stream import _clients, register, unregister, update_symbols


class TestClientRegistry:
    @pytest.mark.asyncio
    async def test_register_and_unregister(self) -> None:
        mock_ws = AsyncMock()
        await register(mock_ws, {"AAPL", "MSFT"})
        assert mock_ws in _clients
        assert _clients[mock_ws] == {"AAPL", "MSFT"}

        await unregister(mock_ws)
        assert mock_ws not in _clients

    @pytest.mark.asyncio
    async def test_update_symbols_replaces(self) -> None:
        mock_ws = AsyncMock()
        await register(mock_ws, {"AAPL"})
        await update_symbols(mock_ws, {"TSLA"})
        assert _clients[mock_ws] == {"TSLA"}
        await unregister(mock_ws)


@pytest.mark.asyncio
async def test_broadcast_sends_quotes() -> None:
    mock_ws = AsyncMock()
    await register(mock_ws, {"AAPL"})

    import asyncio

    from app.stream import _broadcast_loop, _collect_symbols

    with patch(
        "app.stream.market_service.get_quote",
        new=AsyncMock(
            return_value=Quote(symbol="AAPL", price=150.0, change_pct=1.5, source="test")
        ),
    ):
        syms = await _collect_symbols()
        assert "AAPL" in syms

        broadcast_task = asyncio.create_task(_broadcast_loop())
        await asyncio.sleep(0.1)
        broadcast_task.cancel()
        try:
            await broadcast_task
        except asyncio.CancelledError:
            pass

        assert mock_ws.send_text.called

    await unregister(mock_ws)
