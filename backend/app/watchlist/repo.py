"""Data-access functions for watchlist items. Session-injected; never commit."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.watchlist.models import WatchlistItem


# symbol 查询前统一大写，保证大小写不敏感的唯一性体验
async def create_item(
    session: AsyncSession,
    symbol: str,
    note: str | None = None,
    target_price: float | None = None,
) -> WatchlistItem:
    item = WatchlistItem(symbol=symbol.upper(), note=note, target_price=target_price)
    session.add(item)
    await session.flush()
    return item


async def list_items(session: AsyncSession) -> list[WatchlistItem]:
    result = await session.execute(
        # id DESC 保证插入顺序（created_at 在同一事务内可能相同）
        select(WatchlistItem).order_by(WatchlistItem.id.desc())
    )
    return list(result.scalars().all())


async def get_item(session: AsyncSession, item_id: int) -> WatchlistItem | None:
    return await session.get(WatchlistItem, item_id)


async def update_item(
    session: AsyncSession,
    item: WatchlistItem,
    note: str | None = None,
    target_price: float | None = None,
) -> WatchlistItem:
    # 仅更新非 None 的字段（PATCH 语义）
    if note is not None:
        item.note = note
    if target_price is not None:
        item.target_price = target_price
    await session.flush()
    return item


async def delete_item(session: AsyncSession, item: WatchlistItem) -> None:
    await session.delete(item)
    await session.flush()
