"""POST /api/risk/check — pre-trade risk validation.
GET /api/risk/{symbol} — post-trade risk analytics.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.risk.analytics import RiskAnalytics, analyze_risk
from app.risk.engine import RiskCheckResult, check_order
from app.trading import repo, service
from app.trading.schemas import OrderRequest

router = APIRouter(prefix="/api/risk", tags=["risk"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]


class RiskCheckRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    order: OrderRequest


@router.post("/check", response_model=RiskCheckResult)
async def check_risk(req: RiskCheckRequest, session: SessionDep) -> RiskCheckResult:
    account = await service.get_account(session)
    order = await repo.create_order(
        session,
        account_id=account.id,
        symbol=req.order.symbol.upper(),
        side=req.order.side,
        qty=req.order.qty,
        order_type=req.order.order_type,
        limit_price=req.order.limit_price,
        stop_price=req.order.stop_price,
        trail_amount=req.order.trail_amount,
        status="pending",
    )
    result = await check_order(session, account, order)
    session.rollback()
    return result


@router.get("/{symbol}", response_model=RiskAnalytics)
async def get_risk(symbol: str) -> RiskAnalytics:
    return await analyze_risk(symbol)
