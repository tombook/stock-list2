"""Strategy editor API — validate + execute user-written strategies.

POST /api/strategies/validate — syntax + safety check
POST /api/strategies/execute — run user code in subprocess with timeout
"""

from __future__ import annotations

from fastapi import APIRouter

from app.strategy_editor.schemas import (
    StrategyExecuteRequest,
    StrategyExecuteResponse,
    StrategyValidateRequest,
    StrategyValidateResponse,
)
from app.strategy_editor.service import run_strategy, validate

router = APIRouter(prefix="/api/strategies", tags=["strategy-editor"])


@router.post("/validate", response_model=StrategyValidateResponse)
async def validate_code(req: StrategyValidateRequest) -> StrategyValidateResponse:
    return validate(req.code)


@router.post("/execute", response_model=StrategyExecuteResponse)
async def execute_strategy(req: StrategyExecuteRequest) -> StrategyExecuteResponse:
    from app.marketdata import service as market_service

    bars = await market_service.get_bars(req.symbol, req.timeframe, req.limit)
    bars_dicts = [
        {
            "ts": b.ts.isoformat() if hasattr(b.ts, "isoformat") else b.ts,
            "open": b.open,
            "high": b.high,
            "low": b.low,
            "close": b.close,
            "volume": b.volume,
        }
        for b in bars.bars
    ]
    return await run_strategy(req.code, bars_dicts)
