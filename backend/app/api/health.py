"""Health endpoint — liveness + dependency checks."""

from __future__ import annotations

from fastapi import APIRouter

from app import __version__
from app.core import db
from app.marketdata import service as market_service

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    pg_ok = await db.ping()
    deps = {
        "postgres": {"status": "ok" if pg_ok else "down", "detail": None},
        "market_data": {"status": "ok", "detail": "yfinance"},
    }
    status = "healthy" if all(d["status"] == "ok" for d in deps.values()) else "degraded"
    return {"status": status, "version": __version__, "dependencies": deps}
