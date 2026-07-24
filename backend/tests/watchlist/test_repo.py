"""Tests for the watchlist repo layer — CRUD against the real Postgres."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.watchlist import repo


@pytest.mark.asyncio
async def test_create_item_persists_symbol_and_optionals(db_session: AsyncSession) -> None:
    item = await repo.create_item(db_session, "aapl", note="bullish", target_price=200.0)
    assert item.id is not None
    assert item.symbol == "AAPL"  # 大写归一化
    assert item.note == "bullish"
    assert item.target_price == 200.0


@pytest.mark.asyncio
async def test_create_item_minimal(db_session: AsyncSession) -> None:
    item = await repo.create_item(db_session, "MSFT")
    assert item.symbol == "MSFT"
    assert item.note is None
    assert item.target_price is None


@pytest.mark.asyncio
async def test_list_items_orders_newest_first(db_session: AsyncSession) -> None:
    await repo.create_item(db_session, "AAPL")
    await repo.create_item(db_session, "MSFT")
    items = await repo.list_items(db_session)
    assert len(items) == 2
    # MSFT 后插入，应排在前面（created_at desc）
    assert items[0].symbol == "MSFT"


@pytest.mark.asyncio
async def test_get_missing_item_returns_none(db_session: AsyncSession) -> None:
    assert await repo.get_item(db_session, 99999) is None


@pytest.mark.asyncio
async def test_update_item_changes_fields(db_session: AsyncSession) -> None:
    item = await repo.create_item(db_session, "GOOG")
    await repo.update_item(db_session, item, note="earnings play", target_price=180.0)
    assert item.note == "earnings play"
    assert item.target_price == 180.0


@pytest.mark.asyncio
async def test_delete_item_removes_it(db_session: AsyncSession) -> None:
    item = await repo.create_item(db_session, "NVDA")
    item_id = item.id
    await repo.delete_item(db_session, item)
    assert await repo.get_item(db_session, item_id) is None
