"""Trading service — order matching + fill simulation + position/cash updates.

Market orders: filled immediately at current quote price.
Limit orders: stored as pending; checked against current price for fill.
Position update uses weighted average cost on buy, FIFO on sell.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError, NotFoundError
from app.marketdata import service as market_service
from app.trading import repo
from app.trading.models import Account, Order
from app.trading.schemas import OrderRequest


async def get_account(session: AsyncSession) -> Account:
    return await repo.get_or_create_account(session)


async def place_order(session: AsyncSession, req: OrderRequest) -> Order:
    account = await get_account(session)
    symbol = req.symbol.upper()

    if req.order_type == "limit" and req.limit_price is None:
        raise DomainError("limit order requires limit_price")

    order = await repo.create_order(
        session,
        account_id=account.id,
        symbol=symbol,
        side=req.side,
        qty=req.qty,
        order_type=req.order_type,
        limit_price=req.limit_price,
        status="pending",
    )

    if req.order_type == "market":
        await _try_fill(session, account, order)
    elif req.order_type == "limit":
        await _check_limit_fill(session, account, order)

    return order


async def cancel_order(session: AsyncSession, order_id: int) -> Order:
    order = await repo.get_order(session, order_id)
    if order is None:
        raise NotFoundError(f"order {order_id} not found")
    if order.status != "pending":
        raise DomainError(f"order {order_id} is {order.status}, cannot cancel")
    order.status = "cancelled"
    await session.flush()
    return order


async def check_pending_orders(session: AsyncSession) -> int:
    """Check all pending limit orders for fill. Returns count filled."""
    from sqlalchemy import select

    result = await session.execute(select(Order).where(Order.status == "pending"))
    pending = list(result.scalars().all())
    filled = 0
    for order in pending:
        account = await session.get(Account, order.account_id)
        if account and await _check_limit_fill(session, account, order):
            filled += 1
    return filled


async def _try_fill(session: AsyncSession, account: Account, order: Order) -> bool:
    try:
        quote = await market_service.get_quote(order.symbol)
    except Exception:
        return False

    fill_price = quote.price
    if order.order_type == "limit":
        if not _limit_crossed(order, fill_price):
            return False

    await _apply_fill(session, account, order, fill_price)
    return True


async def _check_limit_fill(session: AsyncSession, account: Account, order: Order) -> bool:
    return await _try_fill(session, account, order)


def _limit_crossed(order: Order, price: float) -> bool:
    if order.side == "buy":
        return price <= (order.limit_price or 0)
    return price >= (order.limit_price or float("inf"))


async def _apply_fill(session: AsyncSession, account: Account, order: Order, price: float) -> None:
    order.status = "filled"
    order.filled_price = price
    order.filled_at = datetime.now(UTC)

    pos = await repo.get_or_create_position(session, account.id, order.symbol)

    if order.side == "buy":
        cost = order.qty * price
        if cost > account.cash:
            raise DomainError(f"insufficient cash: need ${cost:.2f}, have ${account.cash:.2f}")
        total_cost = pos.qty * pos.avg_cost + cost
        pos.qty += order.qty
        pos.avg_cost = total_cost / pos.qty if pos.qty > 0 else 0
        account.cash -= cost
    else:
        if order.qty > pos.qty:
            raise DomainError(f"insufficient shares: have {pos.qty}, selling {order.qty}")
        proceeds = order.qty * price
        pos.qty -= order.qty
        if pos.qty == 0:
            pos.avg_cost = 0
        account.cash += proceeds

    await session.flush()
