"""本地 bars 缓存——将历史 OHLCV 持久化到 PG，避免重复网络请求。

首次请求写入 PG，后续直接读库。回测参数优化跑 1000 次时只请求网络一次。
Best-effort：DB 不可用时静默降级到网络。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, UniqueConstraint, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.core.logging import get_logger
from app.marketdata.models import Bar, Bars

_log = get_logger(__name__)


class BarCache(Base):
    """单根缓存的 K 线——(symbol, timeframe, ts) 唯一。"""

    __tablename__ = "bars_cache"
    __table_args__ = (UniqueConstraint("symbol", "timeframe", "ts", name="uq_bars_cache"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    symbol: Mapped[str] = mapped_column(String(16), index=True)
    timeframe: Mapped[str] = mapped_column(String(8))
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    open: Mapped[float] = mapped_column(Float)
    high: Mapped[float] = mapped_column(Float)
    low: Mapped[float] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float)
    volume: Mapped[float | None] = mapped_column(Float, default=None)


async def fetch_cached(
    session: AsyncSession, symbol: str, timeframe: str, limit: int
) -> list[BarCache] | None:
    """从 PG 读取缓存的 bars（最近 limit 根，升序）。None = 无缓存或 DB 错误。"""
    try:
        result = await session.execute(
            select(BarCache)
            .where(BarCache.symbol == symbol.upper(), BarCache.timeframe == timeframe)
            .order_by(BarCache.ts.desc())
            .limit(limit)
        )
        rows = list(result.scalars().all())
        if not rows:
            return None
        rows.reverse()
        return rows
    except SQLAlchemyError:
        return None


def cached_to_bars(rows: list[BarCache], symbol: str, timeframe: str) -> Bars:
    bars = [
        Bar(ts=r.ts, open=r.open, high=r.high, low=r.low, close=r.close, volume=r.volume)
        for r in rows
    ]
    return Bars(symbol=symbol.upper(), timeframe=timeframe, bars=bars, source="cache")


async def upsert_bars(session: AsyncSession, bars: Bars) -> None:
    """将网络获取的 bars 批量写入 PG 缓存（ON CONFLICT DO NOTHING）。"""
    try:
        stmt = text(
            "INSERT INTO bars_cache (symbol, timeframe, ts, open, high, low, close, volume) "
            "VALUES (:sym, :tf, :ts, :o, :h, :l, :c, :v) "
            "ON CONFLICT (symbol, timeframe, ts) DO NOTHING"
        )
        for b in bars.bars:
            await session.execute(
                stmt.bindparams(
                    sym=bars.symbol,
                    tf=bars.timeframe,
                    ts=b.ts,
                    o=b.open,
                    h=b.high,
                    l=b.low,
                    c=b.close,
                    v=b.volume,
                )
            )
        await session.commit()
    except SQLAlchemyError as exc:
        await session.rollback()
        _log.warning("bar_cache_upsert_failed", symbol=bars.symbol, error=str(exc))
