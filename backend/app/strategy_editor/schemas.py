"""Strategy editor schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class StrategyValidateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1, max_length=50000)


class ValidationIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    line: int
    message: str


class StrategyValidateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    valid: bool
    issues: list[ValidationIssue]


class StrategyExecuteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    symbol: str = Field(min_length=1, max_length=16)
    timeframe: str = "1d"
    limit: int = Field(default=252, ge=50, le=1000)


class StrategyExecuteResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    equity: list[dict]
    n_bars: int
    total_return: float
    Sharpe: float
    error: str | None = None
