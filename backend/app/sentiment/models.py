"""Sentiment analysis result model."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class SentimentResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str
    score: float  # -1.0 (very bearish) to +1.0 (very bullish)
    label: str  # "bullish", "bearish", "neutral"
    confidence: float  # 0.0 to 1.0
    article_count: int
    top_headlines: list[str]
    source: str
