"""Pydantic v2 request/response schemas for the backtest API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# Strategy params are heterogeneous (ints, floats, strings) — kept open here;
# the service validates them against the strategy registry's JSON schema.
StrategyParam = int | float | str


class StrategyRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    params: dict[str, StrategyParam] = Field(default_factory=dict)


class BacktestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(min_length=1)
    strategy: StrategyRef
    timeframe: str = "1d"
    limit: int = Field(default=252, ge=50, le=1000)
    cost_bps: float = Field(default=0.0, ge=0.0)
    benchmark: str | None = Field(
        default=None, description="Benchmark symbol (e.g. SPY) for alpha comparison"
    )


class Metrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_return: float
    cagr: float
    sharpe: float
    max_drawdown: float
    win_rate: float
    n_trades: int


class EquityPoint(BaseModel):
    ts: datetime
    equity: float


class BacktestResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str
    strategy: StrategyRef
    timeframe: str
    n_bars: int
    start: datetime
    end: datetime
    metrics: Metrics
    equity: list[EquityPoint]
    benchmark_equity: list[EquityPoint] | None = None
    alpha: float | None = None


class ParamRange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    values: list[StrategyParam]


class OptimizeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(min_length=1)
    strategy: str
    param_ranges: list[ParamRange] = Field(min_length=1)
    timeframe: str = "1d"
    limit: int = Field(default=252, ge=50, le=1000)
    cost_bps: float = Field(default=0.0, ge=0.0)
    target_metric: str = Field(
        default="sharpe", description="Sort results by this metric (sharpe/total_return/max_drawdown)"
    )


class OptimizeRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    params: dict[str, StrategyParam]
    total_return: float
    sharpe: float
    max_drawdown: float
    n_trades: int


class OptimizeResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str
    strategy: str
    target_metric: str
    rows: list[OptimizeRow]
    best: OptimizeRow | None
