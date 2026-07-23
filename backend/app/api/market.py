"""Market-data endpoints — thin pass-through to the service layer."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.marketdata import service as market_service

router = APIRouter(prefix="/api", tags=["market"])


@router.get("/quote/{symbol}")
async def get_quote(symbol: str) -> dict:
    return (await market_service.get_quote(symbol)).model_dump(mode="json")


@router.get("/bars/{symbol}")
async def get_bars(
    symbol: str,
    timeframe: str = Query("1d", description="OHLCV interval: 1d, 1wk, 1mo, 1h, 5m, ..."),
    limit: int = Query(120, ge=1, le=1000),
) -> dict:
    return (await market_service.get_bars(symbol, timeframe, limit)).model_dump(mode="json")
