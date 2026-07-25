"""Pydantic schemas for the trading API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OrderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(min_length=1, max_length=16)
    side: str = Field(pattern="^(buy|sell)$")
    qty: float = Field(gt=0)
    order_type: str = Field(default="market", pattern="^(market|limit)$")
    limit_price: float | None = None


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    symbol: str
    side: str
    qty: float
    order_type: str
    limit_price: float | None
    status: str
    filled_price: float | None
    filled_at: datetime | None
    created_at: datetime


class PositionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    symbol: str
    qty: float
    avg_cost: float
    updated_at: datetime


class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cash: float
    initial_cash: float
    created_at: datetime
