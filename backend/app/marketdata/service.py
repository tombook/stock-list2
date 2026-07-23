"""Market-data service — the public face of the data layer.

Adds short-lived TTL caching so repeated requests for the same quote/bars don't
hit the network. Higher layers (API, future agent tools) call only this module.
"""

from __future__ import annotations

from app.marketdata import registry
from app.marketdata.cache import TTLCache
from app.marketdata.models import Bars, Quote

_quote_cache: TTLCache[Quote] = TTLCache(ttl_seconds=15.0)
_bars_cache: TTLCache[Bars] = TTLCache(ttl_seconds=60.0)


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
    bars = await registry.bars(key.split(":")[0], timeframe, limit)
    _bars_cache.set(key, bars)
    return bars
