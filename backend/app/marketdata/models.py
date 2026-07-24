"""Typed market-data models. These are the canonical shapes every layer speaks."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class AssetClass(str, Enum):
    US_EQUITY = "us_equity"
    HK_EQUITY = "hk_equity"
    A_SHARE = "a_share"
    CRYPTO = "crypto"
    ETF = "etf"
    UNKNOWN = "unknown"


class Quote(BaseModel):
    symbol: str
    price: float
    currency: str | None = None
    name: str | None = None
    change_pct: float | None = None
    as_of: datetime | None = None
    source: str


class Bar(BaseModel):
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None


class Bars(BaseModel):
    symbol: str
    timeframe: str
    bars: list[Bar]
    source: str


class Fundamentals(BaseModel):
    """Company fundamentals snapshot — P/E, market cap, sector, etc.

    Every numeric field is optional: yfinance's `.info` dict is notoriously
    sparse for some tickers (ADRs, small-caps, crypto). We surface what's
    available rather than failing the whole call.
    """

    symbol: str
    name: str | None = None
    sector: str | None = None
    industry: str | None = None
    market_cap: float | None = None
    trailing_pe: float | None = None
    forward_pe: float | None = None
    price_to_book: float | None = None
    dividend_yield: float | None = None
    beta: float | None = None
    fifty_two_week_high: float | None = None
    fifty_two_week_low: float | None = None
    source: str


class CorporateAction(BaseModel):
    """A corporate action event (split, dividend)."""

    date: datetime
    type: str  # "split" or "dividend"
    value: float  # ratio for splits, amount for dividends
    symbol: str
    source: str
