"""SQLAlchemy ORM model for a watchlist item.

A watchlist item tracks a single symbol the user is interested in, optionally
with a note and a target price. Designed to be lightweight — the symbol is the
key payload; everything else is optional context.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class WatchlistItem(Base):
    """One tracked symbol on the user's watchlist."""

    __tablename__ = "watchlist_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

    symbol: Mapped[str] = mapped_column(String(16), index=True)
    note: Mapped[str | None] = mapped_column(Text, default=None)
    target_price: Mapped[float | None] = mapped_column(Float, default=None)
