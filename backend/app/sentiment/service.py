"""Sentiment service — orchestrates news fetch + scoring pipeline.

Flow:
  1. Fetch latest news headlines via yfinance
  2. Try LLM-based scoring (primary, nuanced)
  3. Fall back to keyword-based scoring (always available)
  4. Aggregate into a SentimentResult
"""

from __future__ import annotations

from app.sentiment.models import SentimentResult
from app.sentiment.news import fetch_news
from app.sentiment.scorers import keyword_score, llm_score


def _label(score: float) -> str:
    if score > 0.15:
        return "bullish"
    if score < -0.15:
        return "bearish"
    return "neutral"


async def analyze_sentiment(symbol: str) -> SentimentResult:
    items = await fetch_news(symbol.upper(), limit=10)
    headlines = [it.title for it in items]

    # Try LLM first (nuanced), fall back to keyword
    result = await llm_score(headlines)
    if result is not None:
        score, confidence = result
        source = "llm"
    else:
        score, confidence = keyword_score(headlines)
        source = "keyword"

    return SentimentResult(
        symbol=symbol.upper(),
        score=round(score, 4),
        label=_label(score),
        confidence=round(confidence, 4),
        article_count=len(headlines),
        top_headlines=headlines[:3],
        source=source,
    )
