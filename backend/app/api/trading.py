"""POST/GET/DELETE /api/trading — paper trading CRUD."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.trading import repo, service
from app.trading.schemas import (
    AccountOut,
    OrderOut,
    OrderRequest,
    PositionOut,
)

router = APIRouter(prefix="/api/trading", tags=["trading"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("/account", response_model=AccountOut)
async def get_account(session: SessionDep) -> AccountOut:
    account = await service.get_account(session)
    await session.commit()
    return account


@router.post("/orders", response_model=OrderOut)
async def place_order(req: OrderRequest, session: SessionDep) -> OrderOut:
    order = await service.place_order(session, req)
    await session.commit()
    return order


@router.get("/orders", response_model=list[OrderOut])
async def list_orders(session: SessionDep) -> list[OrderOut]:
    account = await service.get_account(session)
    orders = await repo.list_orders(session, account.id)
    return orders  # type: ignore[return-value]


@router.delete("/orders/{order_id}", response_model=OrderOut)
async def cancel_order(order_id: int, session: SessionDep) -> OrderOut:
    order = await service.cancel_order(session, order_id)
    await session.commit()
    return order


@router.get("/positions", response_model=list[PositionOut])
async def list_positions(session: SessionDep) -> list[PositionOut]:
    account = await service.get_account(session)
    positions = await repo.list_positions(session, account.id)
    return positions  # type: ignore[return-value]
