"""Source registry — ordered fallback chain per request.

The chain is tried in order; the first source that classifies the symbol AND
succeeds wins. Failures (NotFoundError / UpstreamError) fall through to the next.
Add new sources (akshare for A-shares, ccxt for crypto) by implementing the
DataSource protocol and appending here.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.errors import NotFoundError, UpstreamError
from app.marketdata.models import Bars, CorporateAction, Fundamentals, Quote
from app.marketdata.sources import yfinance_src


@dataclass(frozen=True)
class _Source:
    name: str
    classify: callable  # type: ignore[type-arg]
    quote: callable  # type: ignore[type-arg]
    bars: callable  # type: ignore[type-arg]
    fundamentals: callable  # type: ignore[type-arg]
    actions: callable  # type: ignore[type-arg]


# Order matters: most-reliable first. yfinance is currently the only wired source.
_SOURCES: list[_Source] = [
    _Source(
        yfinance_src._NAME,
        yfinance_src.classify,
        yfinance_src.quote,
        yfinance_src.bars,
        yfinance_src.fundamentals,
        yfinance_src.actions,
    ),
]


async def quote(symbol: str) -> Quote:
    failures: list[str] = []
    for src in _SOURCES:
        try:
            return await src.quote(symbol)
        except NotFoundError as exc:
            failures.append(f"{src.name}: {exc.message}")
        except UpstreamError as exc:
            failures.append(f"{src.name}: {exc.message}")
    raise NotFoundError(f"no source served quote for {symbol}; {' | '.join(failures)}")


async def bars(symbol: str, timeframe: str, limit: int) -> Bars:
    failures: list[str] = []
    for src in _SOURCES:
        try:
            return await src.bars(symbol, timeframe, limit)
        except NotFoundError as exc:
            failures.append(f"{src.name}: {exc.message}")
        except UpstreamError as exc:
            failures.append(f"{src.name}: {exc.message}")
    raise NotFoundError(f"no source served bars for {symbol}; {' | '.join(failures)}")


async def fundamentals(symbol: str) -> Fundamentals:
    failures: list[str] = []
    for src in _SOURCES:
        try:
            return await src.fundamentals(symbol)
        except NotFoundError as exc:
            failures.append(f"{src.name}: {exc.message}")
        except UpstreamError as exc:
            failures.append(f"{src.name}: {exc.message}")
    raise NotFoundError(f"no source served fundamentals for {symbol}; {' | '.join(failures)}")


async def actions(symbol: str) -> list[CorporateAction]:
    failures: list[str] = []
    for src in _SOURCES:
        try:
            return await src.actions(symbol)
        except NotFoundError as exc:
            failures.append(f"{src.name}: {exc.message}")
        except UpstreamError as exc:
            failures.append(f"{src.name}: {exc.message}")
    raise NotFoundError(f"no source served actions for {symbol}; {' | '.join(failures)}")
