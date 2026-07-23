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
