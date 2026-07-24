"""Indicator screener — scans multiple symbols against indicator conditions.

Condition DSL examples:
  {"indicator": "rsi", "op": "<", "value": 30}
  {"indicator": "macd", "op": "cross_up", "value": null}
  {"indicator": "bb_lower", "op": ">", "value": null}

Conditions are AND-combined. Each symbol's bars are fetched, indicators computed,
and the latest value checked against the condition.
"""

from __future__ import annotations

import asyncio

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from app.core.errors import DomainError
from app.indicators.registry import compute
from app.marketdata import service as market_service
from app.marketdata.models import Bars

StrategyParam = int | float | str


class ScanCondition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    indicator: str
    op: str = Field(description="lt, gt, cross_up, cross_down")
    value: float | None = None
    params: dict[str, StrategyParam] = Field(default_factory=dict)


class ScanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbols: list[str] = Field(min_length=1, max_length=20)
    timeframe: str = "1d"
    limit: int = Field(default=120, ge=50, le=500)
    conditions: list[ScanCondition] = Field(min_length=1)


class ScanMatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str
    values: dict[str, float | None]


class ScanResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    matched: list[ScanMatch]
    total_checked: int
    matched_count: int


_OPS = {"lt", "gt", "cross_up", "cross_down"}


def _check_condition(series: pd.Series, op: str, value: float | None) -> bool:
    if len(series) < 2:
        return False
    latest = series.iloc[-1]
    prev = series.iloc[-2]
    if pd.isna(latest):
        return False
    if op == "lt":
        return latest < (value if value is not None else 0)
    if op == "gt":
        return latest > (value if value is not None else 0)
    if op == "cross_up":
        return (
            bool(not pd.isna(prev) and prev <= 0 and latest > 0)
            if value is None
            else bool(not pd.isna(prev) and prev <= value and latest > value)
        )
    if op == "cross_down":
        return (
            bool(not pd.isna(prev) and prev >= 0 and latest < 0)
            if value is None
            else bool(not pd.isna(prev) and prev >= value and latest < value)
        )
    return False


async def run_scan(req: ScanRequest) -> ScanResult:
    for cond in req.conditions:
        if cond.op not in _OPS:
            raise DomainError(f"invalid operator: {cond.op}, must be one of {_OPS}")

    async def _check_symbol(sym: str) -> ScanMatch | None:
        try:
            bars = await market_service.get_bars(sym, req.timeframe, req.limit)
        except Exception:
            return None
        df = _bars_to_df(bars)
        values: dict[str, float | None] = {}
        for cond in req.conditions:
            result = compute(cond.indicator, df, **cond.params)
            if hasattr(result, "iloc"):
                series = result
            elif hasattr(result, "__getitem__"):
                col = list(result.columns)[0] if hasattr(result, "columns") else None
                series = result[col] if col else result.iloc[:, 0]
            else:
                return None
            latest = series.iloc[-1] if len(series) > 0 else None
            values[cond.indicator] = None if pd.isna(latest) else float(latest)
            if not _check_condition(series, cond.op, cond.value):
                return None
        return ScanMatch(symbol=sym, values=values)

    tasks = [_check_symbol(s) for s in req.symbols]
    matches = [r for r in await asyncio.gather(*tasks) if r is not None]
    return ScanResult(
        matched=matches,
        total_checked=len(req.symbols),
        matched_count=len(matches),
    )


def _bars_to_df(bars: Bars) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "ts": b.ts,
                "open": b.open,
                "high": b.high,
                "low": b.low,
                "close": b.close,
                "volume": b.volume,
            }
            for b in bars.bars
        ]
    )
