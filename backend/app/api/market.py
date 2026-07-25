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


@router.get("/fundamentals/{symbol}")
async def get_fundamentals(symbol: str) -> dict:
    return (await market_service.get_fundamentals(symbol)).model_dump(mode="json")


@router.get("/actions/{symbol}")
async def get_actions(symbol: str) -> list[dict]:
    actions = await market_service.get_actions(symbol)
    return [a.model_dump(mode="json") for a in actions]


@router.get("/sentiment/{symbol}")
async def get_sentiment(symbol: str) -> dict:
    from app.sentiment.service import analyze_sentiment

    result = await analyze_sentiment(symbol)
    return result.model_dump(mode="json")


@router.get("/predict/{symbol}")
async def get_prediction(
    symbol: str, horizon: int = Query(5, ge=1, le=30)
) -> dict:
    from app.ml.service import predict_direction

    result = await predict_direction(symbol, horizon)
    return result.model_dump(mode="json")
