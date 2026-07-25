"""Alpaca Markets data source — US equity real-time + historical data.

Only active when ALPACA_API_KEY + ALPACA_SECRET_KEY are configured.
Implements the same interface as yfinance_src for transparent fallback.
Register order: Alpaca first (if configured), yfinance as fallback.
"""

from __future__ import annotations

from datetime import UTC, datetime

import httpx

from app.core.errors import NotFoundError, UpstreamError
from app.core.settings import get_settings
from app.marketdata.models import AssetClass, Bar, Bars, Quote

_NAME = "alpaca"
_BASE_URL = "https://data.alpaca.markets/v2"

_TF_MAP = {
    "1d": "1Day",
    "1wk": "1Week",
    "1mo": "1Month",
    "1h": "1Hour",
    "30m": "30Min",
    "15m": "15Min",
    "5m": "5Min",
    "1m": "1Min",
}


def is_configured() -> bool:
    s = get_settings()
    return bool(s.alpaca_api_key and s.alpaca_secret_key)


def _headers() -> dict[str, str]:
    s = get_settings()
    return {
        "APCA-API-KEY-ID": s.alpaca_api_key,
        "APCA-API-SECRET-KEY": s.alpaca_secret_key,
    }


def classify(symbol: str) -> AssetClass | None:
    sym = symbol.upper()
    if sym.endswith((".HK", ".SS", ".SZ")):
        return None
    if "-" in sym and sym.split("-")[-1] in {"USD", "USDT", "BTC"}:
        return None
    return AssetClass.US_EQUITY


async def quote(symbol: str) -> Quote:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{_BASE_URL}/stocks/{symbol}/quotes/latest",
                headers=_headers(),
            )
            resp.raise_for_status()
            data = resp.json()
            q = data.get("quote", {})
            price = q.get("ap") or q.get("bp")
            if price is None:
                raise NotFoundError(f"no alpaca quote for {symbol}")
            return Quote(
                symbol=symbol.upper(),
                price=float(price),
                currency="USD",
                source=_NAME,
                as_of=datetime.now(UTC),
            )
    except (NotFoundError, UpstreamError):
        raise
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise NotFoundError(f"alpaca: symbol {symbol} not found") from exc
        raise UpstreamError(f"alpaca quote failed: {exc.response.status_code}") from exc
    except Exception as exc:
        raise UpstreamError(f"alpaca quote failed for {symbol}: {exc}") from exc


async def bars(symbol: str, timeframe: str, limit: int) -> Bars:
    tf = _TF_MAP.get(timeframe, "1Day")
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{_BASE_URL}/stocks/{symbol}/bars",
                headers=_headers(),
                params={"timeframe": tf, "limit": limit, "adjustment": "raw"},
            )
            resp.raise_for_status()
            data = resp.json()
            raw = data.get("bars", [])
            if not raw:
                raise NotFoundError(f"no alpaca bars for {symbol}")

            rows = [
                Bar(
                    ts=datetime.fromisoformat(b["t"].replace("Z", "+00:00")),
                    open=float(b["o"]),
                    high=float(b["h"]),
                    low=float(b["l"]),
                    close=float(b["c"]),
                    volume=float(b["v"]) if b.get("v") else None,
                )
                for b in raw
            ]
            return Bars(symbol=symbol.upper(), timeframe=timeframe, bars=rows, source=_NAME)
    except (NotFoundError, UpstreamError):
        raise
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise NotFoundError(f"alpaca: symbol {symbol} not found") from exc
        raise UpstreamError(f"alpaca bars failed: {exc.response.status_code}") from exc
    except Exception as exc:
        raise UpstreamError(f"alpaca bars failed for {symbol}: {exc}") from exc


async def fundamentals(symbol: str):
    raise NotFoundError(f"alpaca does not serve fundamentals for {symbol}")


async def actions(symbol: str):
    raise NotFoundError(f"alpaca does not serve actions for {symbol}")
