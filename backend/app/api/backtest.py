"""POST /api/backtest — thin router that delegates to the backtest service."""

from __future__ import annotations

from fastapi import APIRouter

from app.backtest.schemas import BacktestRequest, BacktestResponse
from app.backtest.service import run_backtest

router = APIRouter(prefix="/api", tags=["backtest"])


@router.post("/backtest")
async def backtest(req: BacktestRequest) -> BacktestResponse:
    return await run_backtest(req)
