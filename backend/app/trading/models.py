"""Paper trading ORM models — accounts, orders, positions.

Single-account design (one paper account per deployment). Orders track the
full lifecycle (pending→filled/cancelled). Positions track holdings with
average cost for PnL calculation.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Account(Base):
    __tablename__ = "trading_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    cash: Mapped[float] = mapped_column(Float, default=100_000.0)
    initial_cash: Mapped[float] = mapped_column(Float, default=100_000.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class Order(Base):
    __tablename__ = "trading_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    account_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("trading_accounts.id"), index=True
    )
    symbol: Mapped[str] = mapped_column(String(16), index=True)
    side: Mapped[str] = mapped_column(String(4))  # "buy" or "sell"
    qty: Mapped[float] = mapped_column(Float)
    order_type: Mapped[str] = mapped_column(String(16))
    limit_price: Mapped[float | None] = mapped_column(Float, default=None)
    stop_price: Mapped[float | None] = mapped_column(Float, default=None)
    trail_amount: Mapped[float | None] = mapped_column(Float, default=None)
    trail_high_water: Mapped[float | None] = mapped_column(Float, default=None)
    status: Mapped[str] = mapped_column(String(10), default="pending", index=True)
    filled_price: Mapped[float | None] = mapped_column(Float, default=None)
    filled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class Position(Base):
    __tablename__ = "trading_positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("trading_accounts.id"), index=True)
    symbol: Mapped[str] = mapped_column(String(16), index=True)
    qty: Mapped[float] = mapped_column(Float, default=0.0)
    avg_cost: Mapped[float] = mapped_column(Float, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
