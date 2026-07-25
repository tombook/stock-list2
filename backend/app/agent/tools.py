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


async def _compare_stocks(args: dict[str, Any]) -> dict[str, Any]:
    symbols = [str(s) for s in args["symbols"]]
    results = []
    for sym in symbols[:6]:
        try:
            fund = await market_service.get_fundamentals(sym)
            results.append(fund.model_dump(mode="json"))
        except Exception:
            results.append({"symbol": sym.upper(), "error": "data unavailable"})
    return {"comparison": results}


async def _screen_stocks(args: dict[str, Any]) -> dict[str, Any]:
    import asyncio

    symbols = [str(s) for s in args["symbols"]]
    pe_max = args.get("pe_max")
    sector = args.get("sector")
    min_market_cap = args.get("min_market_cap")

    async def _check(sym: str) -> dict[str, Any] | None:
        try:
            fund = await market_service.get_fundamentals(sym)
        except Exception:
            return None
        if pe_max is not None and fund.trailing_pe is not None:
            if fund.trailing_pe > pe_max:
                return None
        if sector is not None and fund.sector:
            if sector.lower() not in fund.sector.lower():
                return None
        if min_market_cap is not None and fund.market_cap is not None:
            if fund.market_cap < min_market_cap:
                return None
        return {
            "symbol": fund.symbol,
            "name": fund.name,
            "sector": fund.sector,
            "trailing_pe": fund.trailing_pe,
            "market_cap": fund.market_cap,
        }

    tasks = [_check(s) for s in symbols[:10]]
    matches = [r for r in await asyncio.gather(*tasks) if r is not None]
    return {"matches": matches, "total_checked": len(symbols), "matched": len(matches)}


async def _get_sentiment(args: dict[str, Any]) -> dict[str, Any]:
    from app.sentiment.service import analyze_sentiment

    result = await analyze_sentiment(str(args["symbol"]))
    return result.model_dump(mode="json")


async def _predict_direction(args: dict[str, Any]) -> dict[str, Any]:
    from app.ml.service import predict_direction

    result = await predict_direction(
        str(args["symbol"]), int(args.get("horizon") or 5)
    )
    return result.model_dump(mode="json")


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

_COMPARE_PARAMS = {
    "type": "object",
    "properties": {
        "symbols": {
            "type": "array",
            "items": {"type": "string"},
            "description": "2-6 tickers to compare, e.g. [\"AAPL\", \"MSFT\", \"GOOG\"]",
            "minItems": 2,
            "maxItems": 6,
        }
    },
    "required": ["symbols"],
    "additionalProperties": False,
}

_SCREEN_PARAMS = {
    "type": "object",
    "properties": {
        "symbols": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Tickers to screen, e.g. [\"AAPL\", \"MSFT\", \"TSLA\"]",
            "minItems": 1,
            "maxItems": 10,
        },
        "pe_max": {"type": "number", "description": "Maximum trailing P/E ratio"},
        "sector": {"type": "string", "description": "Sector filter (case-insensitive substring)"},
        "min_market_cap": {
            "type": "number",
            "description": "Minimum market cap in USD (e.g. 1e12 for $1T)",
        },
    },
    "required": ["symbols"],
    "additionalProperties": False,
}

_PREDICT_PARAMS = {
    "type": "object",
    "properties": {
        "symbol": {"type": "string", "description": "Ticker, e.g. AAPL"},
        "horizon": {"type": "integer", "minimum": 1, "maximum": 30, "default": 5},
    },
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
        "compare_stocks": Tool(
            "compare_stocks",
            "Compare fundamentals of up to 6 stocks side by side.",
            _COMPARE_PARAMS,
            _compare_stocks,
        ),
        "screen_stocks": Tool(
            "screen_stocks",
            "Screen stocks by fundamental criteria (P/E max, sector, market cap).",
            _SCREEN_PARAMS,
            _screen_stocks,
        ),
        "get_sentiment": Tool(
            "get_sentiment",
            "Get market sentiment for a symbol based on recent news headlines.",
            _QUOTE_PARAMS,
            _get_sentiment,
        ),
        "predict_direction": Tool(
            "predict_direction",
            "Predict the probability of price increase using ML (AdaBoost) with feature importance.",
            _PREDICT_PARAMS,
            _predict_direction,
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
