"""CRUD endpoints for the watchlist — POST/GET/PATCH/DELETE on /api/watchlist."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.errors import NotFoundError
from app.watchlist import repo
from app.watchlist.models import WatchlistItem
from app.watchlist.schemas import WatchlistCreate, WatchlistItemOut, WatchlistUpdate

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("", response_model=list[WatchlistItemOut])
async def list_watchlist(session: SessionDep) -> list[WatchlistItem]:
    return await repo.list_items(session)


@router.post("", response_model=WatchlistItemOut, status_code=201)
async def add_item(body: WatchlistCreate, session: SessionDep) -> WatchlistItem:
    item = await repo.create_item(session, body.symbol, body.note, body.target_price)
    await session.commit()
    return item


@router.patch("/{item_id}", response_model=WatchlistItemOut)
async def patch_item(
    item_id: int, body: WatchlistUpdate, session: SessionDep
) -> WatchlistItem:
    item = await repo.get_item(session, item_id)
    if item is None:
        raise NotFoundError(f"watchlist item {item_id} not found")
    await repo.update_item(session, item, body.note, body.target_price)
    await session.commit()
    return item


@router.delete("/{item_id}", status_code=204)
async def remove_item(item_id: int, session: SessionDep) -> None:
    item = await repo.get_item(session, item_id)
    if item is None:
        raise NotFoundError(f"watchlist item {item_id} not found")
    await repo.delete_item(session, item)
    await session.commit()
