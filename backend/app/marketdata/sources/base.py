"""DataSource protocol — every market-data source implements this.

The registry picks a source per symbol and falls back through the chain on failure.
Adding a source = implement this protocol + register it in registry.get_registry().
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.marketdata.models import AssetClass, Bars, Quote


@runtime_checkable
class DataSource(Protocol):
    name: str

    def classify(self, symbol: str) -> AssetClass | None:
        """Return the asset class this source serves for the symbol, or None."""
        ...

    async def quote(self, symbol: str) -> Quote: ...

    async def bars(self, symbol: str, timeframe: str, limit: int) -> Bars: ...
