"""Pattern detection API + agent tool."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from app.chart_pattern.service import detect_patterns

router = APIRouter(prefix="/api/patterns", tags=["chart-patterns"])


class PatternOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    type: str
    confidence: float
    description: str
    key_levels: list[float] = Field(default_factory=list)


class PatternResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str
    timeframe: str
    n_bars: int
    patterns: list[PatternOut]
    summary: str
    source: str


@router.get("/{symbol}/detect", response_model=PatternResult)
async def detect(symbol: str, timeframe: str = "1d", limit: int = 60) -> PatternResult:
    result = await detect_patterns(symbol, timeframe, limit)
    return result
