"""yfinance source — covers US/HK equities, ETFs, and many crypto pairs.

yfinance is synchronous and network-bound, so all calls are offloaded to a thread
via asyncio.to_thread. This keeps the FastAPI event loop unblocked.
"""

from __future__ import annotations

import asyncio
from datetime import datetime

import yfinance

from app.core.errors import NotFoundError, UpstreamError
from app.marketdata.models import AssetClass, Bar, Bars, Quote

_NAME = "yfinance"


def classify(symbol: str) -> AssetClass | None:
    sym = symbol.upper()
    if sym.endswith(".HK"):
        return AssetClass.HK_EQUITY
    if sym.endswith((".SS", ".SZ")):
        return AssetClass.A_SHARE
    if "-" in sym and sym.split("-")[-1] in {"USD", "USDT", "BTC", "EUR", "GBP"}:
        return AssetClass.CRYPTO
    if sym.startswith(("^",)) or sym in {"SPY", "QQQ", "DIA", "IWM"}:
        return AssetClass.ETF
    # yfinance is the broad fallback for US-listed tickers.
    return AssetClass.US_EQUITY


def _safe_float(value: object) -> float | None:
    try:
        if value is None:
            return None
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


async def quote(symbol: str) -> Quote:
    def _fetch() -> Quote:
        info = yfinance.Ticker(symbol).fast_info
        price = _safe_float(getattr(info, "last_price", None))
        if price is None:
            raise NotFoundError(f"no quote for {symbol}")
        prev = _safe_float(getattr(info, "previous_close", None))
        change = ((price - prev) / prev * 100.0) if (prev and prev != 0) else None
        return Quote(
            symbol=symbol.upper(),
            price=price,
            currency=getattr(info, "currency", None),
            change_pct=change,
            source=_NAME,
        )

    try:
        return await asyncio.to_thread(_fetch)
    except (NotFoundError, UpstreamError):
        raise
    except Exception as exc:  # yfinance raises a wide variety of errors
        raise UpstreamError(f"{_NAME} quote failed for {symbol}: {exc}") from exc


async def bars(symbol: str, timeframe: str, limit: int) -> Bars:
    interval = timeframe or "1d"

    def _fetch() -> Bars:
        # Map a desired row count to a yfinance period string, then tail() to size.
        if interval.endswith(("m", "h")):
            period = "5d" if interval.endswith("m") else "60d"
        elif interval == "1wk":
            period = f"{max(limit, 4) * 7}d"
        elif interval == "1mo":
            period = f"{max(limit, 1) * 31}d"
        else:
            period = f"{max(limit, 1)}d"
        df = yfinance.Ticker(symbol).history(period=period, interval=interval)
        if df is None or df.empty:
            raise NotFoundError(f"no bars for {symbol}")
        df = df.tail(limit)
        rows = []
        for ts, row in df.iterrows():
            rows.append(
                Bar(
                    ts=ts.to_pydatetime(),
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    volume=float(row["Volume"]) if row["Volume"] == row["Volume"] else None,
                )
            )
        return Bars(symbol=symbol.upper(), timeframe=interval, bars=rows, source=_NAME)

    try:
        return await asyncio.to_thread(_fetch)
    except (NotFoundError, UpstreamError):
        raise
    except Exception as exc:
        raise UpstreamError(f"{_NAME} bars failed for {symbol}: {exc}") from exc
