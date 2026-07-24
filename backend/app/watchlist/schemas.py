"""Pydantic response schemas for the watchlist API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WatchlistCreate(BaseModel):
    """Request body for adding a watchlist item."""

    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(min_length=1, max_length=16)
    note: str | None = None
    target_price: float | None = Field(default=None, ge=0)


class WatchlistUpdate(BaseModel):
    """Request body for patching a watchlist item."""

    model_config = ConfigDict(extra="forbid")

    note: str | None = None
    target_price: float | None = Field(default=None, ge=0)


class WatchlistItemOut(BaseModel):
    """Response shape for a watchlist item."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    symbol: str
    note: str | None
    target_price: float | None
    created_at: datetime
