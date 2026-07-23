"""Agent tools — a small, hand-written registry. Each tool is one async function
plus a JSON-Schema for its parameters, exposed to the LLM in OpenAI function-call
format. Add a tool = add one entry here."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from app.marketdata import service as market_service

Handler = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Handler


async def _get_quote(args: dict[str, Any]) -> dict[str, Any]:
    quote = await market_service.get_quote(str(args["symbol"]))
    return quote.model_dump(mode="json")


async def _get_bars(args: dict[str, Any]) -> dict[str, Any]:
    bars = await market_service.get_bars(
        str(args["symbol"]),
        str(args.get("timeframe") or "1d"),
        int(args.get("limit") or 120),
    )
    return bars.model_dump(mode="json")


_QUOTE_PARAMS = {
    "type": "object",
    "properties": {"symbol": {"type": "string", "description": "Ticker, e.g. AAPL, 0700.HK"}},
    "required": ["symbol"],
    "additionalProperties": False,
}

_BARS_PARAMS = {
    "type": "object",
    "properties": {
        "symbol": {"type": "string"},
        "timeframe": {"type": "string", "description": "1d, 1wk, 1mo, 1h, 5m", "default": "1d"},
        "limit": {"type": "integer", "minimum": 1, "maximum": 1000, "default": 120},
    },
    "required": ["symbol"],
    "additionalProperties": False,
}


def registry() -> dict[str, Tool]:
    return {
        "get_quote": Tool(
            "get_quote",
            "Get the latest price quote for a market symbol.",
            _QUOTE_PARAMS,
            _get_quote,
        ),
        "get_bars": Tool(
            "get_bars",
            "Get historical OHLCV bars for a market symbol.",
            _BARS_PARAMS,
            _get_bars,
        ),
    }


def openai_tools() -> list[dict[str, Any]]:
    return [
        {"type": "function", "function": {"name": t.name, "description": t.description, "parameters": t.parameters}}
        for t in registry().values()
    ]
