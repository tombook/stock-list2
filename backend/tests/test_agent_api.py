"""POST /api/analyze — streams SSE; LLM stubbed."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.agent import llm as llm_mod
from app.main import app
from app.marketdata import service as market_service
from app.marketdata.models import Quote

_TOOL_MESSAGE = {
    "role": "assistant",
    "content": None,
    "tool_calls": [
        {"id": "c1", "type": "function", "function": {"name": "get_quote", "arguments": '{"symbol":"AAPL"}'}}
    ],
}
_FINAL_MESSAGE = {"role": "assistant", "content": "done", "tool_calls": None}


@pytest.fixture
async def client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def test_analyze_streams_tool_call_then_final(client: httpx.AsyncClient) -> None:
    fake = Quote(symbol="AAPL", price=1.0, source="test")
    with (
        patch.object(llm_mod, "chat", new=AsyncMock(side_effect=[_TOOL_MESSAGE, _FINAL_MESSAGE])),
        patch.object(market_service, "get_quote", new=AsyncMock(return_value=fake)),
    ):
        resp = await client.post("/api/analyze", json={"prompt": "price of AAPL"})

    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")
    text = resp.text
    assert "event: tool_call" in text
    assert "event: tool_result" in text
    assert "event: final" in text
    assert "event: done" in text


async def test_analyze_reports_error_event_when_llm_unconfigured(client: httpx.AsyncClient) -> None:
    with patch.object(llm_mod, "chat", new=AsyncMock(side_effect=Exception("no key"))):
        resp = await client.post("/api/analyze", json={"prompt": "hi"})
    assert resp.status_code == 200
    assert "event: error" in resp.text
