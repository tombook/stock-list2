"""Trading repo — data access for accounts, orders, positions."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.trading.models import Account, Order, Position


async def get_or_create_account(session: AsyncSession) -> Account:
    result = await session.execute(select(Account).limit(1))
    account = result.scalars().first()
    if account is None:
        account = Account()
        session.add(account)
        await session.flush()
    return account


async def create_order(session: AsyncSession, account_id: int, **kwargs) -> Order:
    order = Order(account_id=account_id, **kwargs)
    session.add(order)
    await session.flush()
    return order


async def list_orders(session: AsyncSession, account_id: int, limit: int = 50) -> list[Order]:
    result = await session.execute(
        select(Order).where(Order.account_id == account_id).order_by(Order.id.desc()).limit(limit)
    )
    return list(result.scalars().all())


async def get_order(session: AsyncSession, order_id: int) -> Order | None:
    return await session.get(Order, order_id)


async def get_position(session: AsyncSession, account_id: int, symbol: str) -> Position | None:
    result = await session.execute(
        select(Position).where(
            Position.account_id == account_id,
            Position.symbol == symbol.upper(),
        )
    )
    return result.scalars().first()


async def list_positions(session: AsyncSession, account_id: int) -> list[Position]:
    result = await session.execute(select(Position).where(Position.account_id == account_id))
    return list(result.scalars().all())


async def get_or_create_position(session: AsyncSession, account_id: int, symbol: str) -> Position:
    pos = await get_position(session, account_id, symbol)
    if pos is None:
        pos = Position(account_id=account_id, symbol=symbol.upper())
        session.add(pos)
        await session.flush()
    return pos
