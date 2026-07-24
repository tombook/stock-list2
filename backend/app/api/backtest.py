"""POST /api/backtest — run a backtest, persist the result best-effort, return it.
POST /api/backtest/optimize — grid search over strategy parameters.

Persistence failure (e.g. a constraint violation) never blocks the response: the
user still gets the computed metrics. The session comes from the standard
dependency so the same transaction context flows as the other routers.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.backtest.optimizer import run_optimize
from app.backtest.schemas import BacktestRequest, BacktestResponse, OptimizeRequest, OptimizeResult
from app.backtest.service import run_backtest
from app.core.db import get_session
from app.core.logging import get_logger
from app.runs import service as runs_service

router = APIRouter(prefix="/api", tags=["backtest"])
_log = get_logger(__name__)

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post("/backtest", response_model=BacktestResponse)
async def backtest(
    req: BacktestRequest,
    session: SessionDep,
) -> BacktestResponse:
    resp = await run_backtest(req)
    try:
        await runs_service.save_run(session, resp, req.cost_bps)
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        _log.warning("backtest_run_persist_failed", symbol=req.symbol)
    return resp


@router.post("/backtest/optimize", response_model=OptimizeResult)
async def optimize(req: OptimizeRequest) -> OptimizeResult:
    return await run_optimize(req)
