"""Market-data service — the public face of the data layer.

Adds short-lived TTL caching so repeated requests for the same quote/bars don't
hit the network. Higher layers (API, future agent tools) call only this module.
get_bars also checks a PG-level cache (bars_cache table) before hitting the network.
"""

from __future__ import annotations

from app.core.logging import get_logger
from app.marketdata import registry
from app.marketdata.cache import TTLCache
from app.marketdata.models import Bars, CorporateAction, Fundamentals, Quote

_log = get_logger(__name__)
_quote_cache: TTLCache[Quote] = TTLCache(ttl_seconds=15.0)
_bars_cache: TTLCache[Bars] = TTLCache(ttl_seconds=60.0)
_fundamentals_cache: TTLCache[Fundamentals] = TTLCache(ttl_seconds=300.0)


async def get_quote(symbol: str) -> Quote:
    key = symbol.upper()
    cached = _quote_cache.get(key)
    if cached is not None:
        return cached
    quote = await registry.quote(key)
    _quote_cache.set(key, quote)
    return quote


async def get_bars(symbol: str, timeframe: str = "1d", limit: int = 120) -> Bars:
    key = f"{symbol.upper()}:{timeframe}:{limit}"
    cached = _bars_cache.get(key)
    if cached is not None:
        return cached

    # Best-effort PG cache check
    bars = await _try_pg_cache(symbol.upper(), timeframe, limit)
    if bars is None:
        bars = await registry.bars(symbol.upper(), timeframe, limit)
        await _try_pg_upsert(bars)

    _bars_cache.set(key, bars)
    return bars


async def _try_pg_cache(symbol: str, timeframe: str, limit: int) -> Bars | None:
    """Check PG for cached bars; return None if unavailable or empty."""
    try:
        from app.core.db import get_session_factory
        from app.marketdata.bar_cache import cached_to_bars, fetch_cached

        factory = get_session_factory()
        async with factory() as session:
            rows = await fetch_cached(session, symbol, timeframe, limit)
            if rows is not None and len(rows) >= min(limit, 10):
                return cached_to_bars(rows, symbol, timeframe)
    except Exception:
        pass  # DB unavailable — silent degrade to network
    return None


async def _try_pg_upsert(bars: Bars) -> None:
    """Best-effort write to PG cache."""
    try:
        from app.core.db import get_session_factory
        from app.marketdata.bar_cache import upsert_bars

        factory = get_session_factory()
        async with factory() as session:
            await upsert_bars(session, bars)
    except Exception:
        pass  # DB unavailable — silent degrade


async def get_fundamentals(symbol: str) -> Fundamentals:
    key = symbol.upper()
    cached = _fundamentals_cache.get(key)
    if cached is not None:
        return cached
    fund = await registry.fundamentals(key)
    _fundamentals_cache.set(key, fund)
    return fund


async def get_actions(symbol: str) -> list[CorporateAction]:
    return await registry.actions(symbol.upper())
