"""Trading service — order matching + fill simulation + position/cash updates.

Supported order types:
  - market: filled immediately at current quote price
  - limit: pending until market price crosses limit_price
  - stop: pending until price hits stop_price, then fills as market
  - stop_limit: pending until stop_price, then converts to limit order
  - trailing_stop: dynamic stop that follows price; trail_amount is $ or %
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

    _validate_request(req)

    order = await repo.create_order(
        session,
        account_id=account.id,
        symbol=symbol,
        side=req.side,
        qty=req.qty,
        order_type=req.order_type,
        limit_price=req.limit_price,
        stop_price=req.stop_price,
        trail_amount=req.trail_amount,
        status="pending",
    )

    if req.order_type == "market":
        await _try_fill(session, account, order)
    else:
        await _check_pending_fill(session, account, order)

    return order


def _validate_request(req: OrderRequest) -> None:
    ot = req.order_type
    if ot in ("limit", "stop_limit") and req.limit_price is None:
        raise DomainError(f"{ot} order requires limit_price")
    if ot in ("stop", "stop_limit") and req.stop_price is None:
        raise DomainError(f"{ot} order requires stop_price")
    if ot == "trailing_stop" and req.trail_amount is None:
        raise DomainError("trailing_stop order requires trail_amount")


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
        if account and await _check_pending_fill(session, account, order):
            filled += 1
    return filled


async def _try_fill(session: AsyncSession, account: Account, order: Order) -> bool:
    try:
        quote = await market_service.get_quote(order.symbol)
    except Exception:
        return False

    price = quote.price

    if order.order_type == "market":
        await _apply_fill(session, account, order, price)
        return True

    if order.order_type == "limit":
        if _limit_crossed(order, price):
            await _apply_fill(session, account, order, price)
            return True
        return False

    if order.order_type == "stop":
        if _stop_triggered(order, price):
            await _apply_fill(session, account, order, price)
            return True
        return False

    if order.order_type == "stop_limit":
        if _stop_triggered(order, price):
            order.order_type = "limit"
            if _limit_crossed(order, price):
                await _apply_fill(session, account, order, price)
                return True
        return False

    if order.order_type == "trailing_stop":
        return await _check_trailing_stop(session, account, order, price)

    return False


async def _check_pending_fill(
    session: AsyncSession, account: Account, order: Order
) -> bool:
    return await _try_fill(session, account, order)


async def _check_trailing_stop(
    session: AsyncSession, account: Account, order: Order, price: float
) -> bool:
    if order.trail_high_water is None:
        order.trail_high_water = price
    elif price > order.trail_high_water:
        order.trail_high_water = price

    trail = order.trail_amount or 0
    if trail < 1:
        threshold = order.trail_high_water * (1 - trail)
    else:
        threshold = order.trail_high_water - trail

    triggered = order.side == "sell" and price <= threshold
    if triggered:
        await _apply_fill(session, account, order, price)
        return True
    await session.flush()
    return False


def _limit_crossed(order: Order, price: float) -> bool:
    if order.side == "buy":
        return price <= (order.limit_price or 0)
    return price >= (order.limit_price or float("inf"))


def _stop_triggered(order: Order, price: float) -> bool:
    sp = order.stop_price or 0
    if order.side == "buy":
        return price >= sp
    return price <= sp


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
