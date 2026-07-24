"""News headline fetcher — uses yfinance's built-in .news (free, no API key)."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from app.core.errors import NotFoundError, UpstreamError


@dataclass(frozen=True)
class NewsItem:
    title: str
    publisher: str


async def fetch_news(symbol: str, limit: int = 10) -> list[NewsItem]:
    def _fetch() -> list[NewsItem]:
        import yfinance

        ticker = yfinance.Ticker(symbol)
        raw = ticker.news
        if not raw:
            raise NotFoundError(f"no news for {symbol}")

        items: list[NewsItem] = []
        for entry in raw[:limit]:
            title = entry.get("title", "")
            publisher = entry.get("publisher", "")
            if title:
                items.append(NewsItem(title=title, publisher=publisher))
        if not items:
            raise NotFoundError(f"no news headlines for {symbol}")
        return items

    try:
        return await asyncio.to_thread(_fetch)
    except (NotFoundError, UpstreamError):
        raise
    except Exception as exc:
        raise UpstreamError(f"news fetch failed for {symbol}: {exc}") from exc
