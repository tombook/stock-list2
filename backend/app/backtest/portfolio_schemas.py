"""Portfolio backtest schemas — multi-symbol equal-weight or custom-weight."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

StrategyParam = int | float | str


class PortfolioBacktestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbols: list[str] = Field(min_length=2, max_length=20)
    timeframe: str = "1d"
    limit: int = Field(default=252, ge=50, le=1000)
    cost_bps: float = Field(default=0.0, ge=0.0)
    rebalance: str = Field(
        default="equal_weight",
        description="equal_weight or custom",
    )
    weights: dict[str, float] | None = Field(
        default=None,
        description="Custom weights per symbol (must sum to ~1.0)",
    )


class PortfolioMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_return: float
    cagr: float
    sharpe: float
    max_drawdown: float
    volatility: float


class PortfolioBacktestResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbols: list[str]
    n_bars: int
    start: datetime
    end: datetime
    rebalance: str
    weights: dict[str, float]
    metrics: PortfolioMetrics
    equity: list[dict]
