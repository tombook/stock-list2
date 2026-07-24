"""Pydantic response schemas for the runs API — never expose the ORM model directly.

`RunSummary` is the list-row shape (no equity curve, no params); `RunDetail` carries
everything needed to replay the equity chart. Both map from the ORM `Run` via
`from_attributes=True`.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.runs.models import EquityRow, StrategyParam


class RunSummary(BaseModel):
    """Lightweight row for the history list."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    symbol: str
    strategy_name: str
    timeframe: str
    n_bars: int
    period_start: datetime
    period_end: datetime
    total_return: float
    sharpe: float
    max_drawdown: float
    n_trades: int
    created_at: datetime


class RunDetail(BaseModel):
    """Full run including params and the equity curve."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    symbol: str
    strategy_name: str
    strategy_params: dict[str, StrategyParam]
    timeframe: str
    cost_bps: float
    n_bars: int
    period_start: datetime
    period_end: datetime
    total_return: float
    cagr: float
    sharpe: float
    max_drawdown: float
    win_rate: float
    n_trades: int
    equity: list[EquityRow]
    created_at: datetime
