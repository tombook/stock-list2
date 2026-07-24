"""SQLAlchemy ORM model for a persisted backtest run.

A run captures the full inputs (symbol/strategy/params/timeframe), the computed
performance metrics, and the complete equity curve so it can be replayed later
without re-fetching market data. Stored as JSON for the variable-length parts
(params, equity) and scalars for the metrics.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

# JSON 列承载异构值（策略参数可能是 int/float/str；equity 点含 ISO 时间戳与浮点权益）。
StrategyParam = int | float | str
EquityRow = dict[str, float | str]


class Run(Base):
    """One executed backtest — inputs, metrics, and the full equity curve."""

    __tablename__ = "runs"

    # auto-generated
    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

    # inputs
    symbol: Mapped[str] = mapped_column(String(16), index=True)
    strategy_name: Mapped[str] = mapped_column(String(32))
    strategy_params: Mapped[dict[str, StrategyParam]] = mapped_column(JSON)
    timeframe: Mapped[str] = mapped_column(String(8))
    cost_bps: Mapped[float] = mapped_column(Float)
    n_bars: Mapped[int] = mapped_column(Integer)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # metrics
    total_return: Mapped[float] = mapped_column(Float)
    cagr: Mapped[float] = mapped_column(Float)
    sharpe: Mapped[float] = mapped_column(Float)
    max_drawdown: Mapped[float] = mapped_column(Float)
    win_rate: Mapped[float] = mapped_column(Float)
    n_trades: Mapped[int] = mapped_column(Integer)

    # full equity curve as [{ts: iso8601, equity: float}, ...]
    equity: Mapped[list[EquityRow]] = mapped_column(JSON)
