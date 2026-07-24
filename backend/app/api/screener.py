"""POST /api/scan — indicator-based stock screener."""

from __future__ import annotations

from fastapi import APIRouter

from app.indicators.screener import ScanRequest, ScanResult, run_scan

router = APIRouter(prefix="/api", tags=["screener"])


@router.post("/scan", response_model=ScanResult)
async def scan(req: ScanRequest) -> ScanResult:
    return await run_scan(req)
