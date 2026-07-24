"""Agent tools — a small, hand-written registry. Each tool is one async function
plus a JSON-Schema for its parameters, exposed to the LLM in OpenAI function-call
format. Add a tool = add one entry here."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from app.backtest.schemas import BacktestRequest, StrategyRef
from app.backtest.service import run_backtest as run_backtest_service
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


async def _get_fundamentals(args: dict[str, Any]) -> dict[str, Any]:
    fund = await market_service.get_fundamentals(str(args["symbol"]))
    return fund.model_dump(mode="json")


async def _run_backtest(args: dict[str, Any]) -> dict[str, Any]:
    req = BacktestRequest(
        symbol=str(args["symbol"]),
        strategy=StrategyRef(
            name=str(args["strategy"]["name"]),
            params=dict(args["strategy"].get("params") or {}),
        ),
        timeframe=str(args.get("timeframe") or "1d"),
        limit=int(args.get("limit") or 252),
        cost_bps=float(args.get("cost_bps") or 0.0),
    )
    resp = await run_backtest_service(req)
    return {
        "symbol": resp.symbol,
        "strategy": resp.strategy.name,
        "timeframe": resp.timeframe,
        "n_bars": resp.n_bars,
        "start": resp.start.isoformat(),
        "end": resp.end.isoformat(),
        "total_return": resp.metrics.total_return,
        "cagr": resp.metrics.cagr,
        "sharpe": resp.metrics.sharpe,
        "max_drawdown": resp.metrics.max_drawdown,
        "win_rate": resp.metrics.win_rate,
        "n_trades": resp.metrics.n_trades,
    }


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

_FUNDAMENTALS_PARAMS = {
    "type": "object",
    "properties": {"symbol": {"type": "string", "description": "Ticker, e.g. AAPL, MSFT"}},
    "required": ["symbol"],
    "additionalProperties": False,
}

_BACKTEST_PARAMS = {
    "type": "object",
    "properties": {
        "symbol": {"type": "string", "description": "Ticker, e.g. AAPL, MSFT"},
        "strategy": {
            "type": "object",
            "description": "Strategy to run.",
            "properties": {
                "name": {
                    "type": "string",
                    "enum": ["sma_cross", "momentum", "buy_hold"],
                    "description": "Which built-in strategy to use.",
                },
                "params": {
                    "type": "object",
                    "description": "Strategy parameters (e.g. {fast:5, slow:20}).",
                },
            },
            "required": ["name"],
            "additionalProperties": False,
        },
        "timeframe": {"type": "string", "default": "1d"},
        "limit": {"type": "integer", "minimum": 50, "maximum": 1000, "default": 252},
        "cost_bps": {"type": "number", "minimum": 0, "default": 0},
    },
    "required": ["symbol", "strategy"],
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
        "get_fundamentals": Tool(
            "get_fundamentals",
            "Get company fundamentals for a market symbol (P/E, market cap, sector, etc.).",
            _FUNDAMENTALS_PARAMS,
            _get_fundamentals,
        ),
        "run_backtest": Tool(
            "run_backtest",
            "Run a backtest of a named strategy on a market symbol and return performance metrics.",
            _BACKTEST_PARAMS,
            _run_backtest,
        ),
    }


def openai_tools() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
            },
        }
        for t in registry().values()
    ]
