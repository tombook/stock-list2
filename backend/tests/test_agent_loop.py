"""Agent loop — LLM and the market service are stubbed, so this is fully offline."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from app.agent import loop
from app.marketdata.models import Quote

_TOOL_MESSAGE = {
    "role": "assistant",
    "content": None,
    "tool_calls": [
        {"id": "c1", "type": "function", "function": {"name": "get_quote", "arguments": '{"symbol":"AAPL"}'}}
    ],
}
_FINAL_MESSAGE = {"role": "assistant", "content": "AAPL trades at 123.0.", "tool_calls": None}


async def test_loop_executes_tool_then_final() -> None:
    fake_quote = Quote(symbol="AAPL", price=123.0, currency="USD", source="test")
    with (
        patch("app.agent.llm.chat", new=AsyncMock(side_effect=[_TOOL_MESSAGE, _FINAL_MESSAGE])),
        patch("app.marketdata.service.get_quote", new=AsyncMock(return_value=fake_quote)),
    ):
        events = [event async for event in loop.run("price of AAPL")]

    types = [e["type"] for e in events]
    assert "tool_call" in types
    assert "tool_result" in types
    assert events[-1]["type"] == "final"
    assert events[-1]["data"]["answer"] == "AAPL trades at 123.0."

    tool_result = next(e for e in events if e["type"] == "tool_result")
    assert tool_result["data"]["ok"] is True
    assert tool_result["data"]["result"]["price"] == 123.0


async def test_loop_surfaces_tool_failure_to_model() -> None:
    error_then_final = [
        _TOOL_MESSAGE,
        {"role": "assistant", "content": "I couldn't fetch the quote.", "tool_calls": None},
    ]
    with (
        patch("app.agent.llm.chat", new=AsyncMock(side_effect=error_then_final)),
        patch("app.marketdata.service.get_quote", new=AsyncMock(side_effect=RuntimeError("boom"))),
    ):
        events = [event async for event in loop.run("price of AAPL")]

    tool_result = next(e for e in events if e["type"] == "tool_result")
    assert tool_result["data"]["ok"] is False
    assert "boom" in tool_result["data"]["result"]["error"]
    assert events[-1]["type"] == "final"
