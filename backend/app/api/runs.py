"""GET /api/runs — history list and detail of persisted backtest runs.

Thin routers delegating to the runs service; returns ORM `Run` objects and lets
FastAPI's `response_model` shape them via `from_attributes=True`.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.errors import NotFoundError
from app.runs import service
from app.runs.models import Run
from app.runs.schemas import RunDetail, RunSummary

router = APIRouter(prefix="/api", tags=["runs"])

# Annotated 依赖注入（PEP 593 / FastAPI 推荐写法）规避 ruff B008，比默认参数调用 Depends 更清晰
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("/runs", response_model=list[RunSummary])
async def list_runs(
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[Run]:
    return await service.fetch_runs(session, limit)


@router.get("/runs/{run_id}", response_model=RunDetail)
async def get_run(run_id: int, session: SessionDep) -> Run:
    run = await service.fetch_run(session, run_id)
    if run is None:
        raise NotFoundError(f"run {run_id} not found")
    return run
