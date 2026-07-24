"""Tests for the sentiment analysis pipeline."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.sentiment.models import SentimentResult
from app.sentiment.news import NewsItem
from app.sentiment.scorers import keyword_score
from app.sentiment.service import _label, analyze_sentiment


class TestKeywordScorer:
    def test_bullish_headlines(self) -> None:
        headlines = ["AAPL beats earnings, surges to record high"]
        score, conf = keyword_score(headlines)
        assert score > 0

    def test_bearish_headlines(self) -> None:
        headlines = ["TSLA plunges after weak delivery numbers"]
        score, conf = keyword_score(headlines)
        assert score < 0

    def test_neutral_headlines(self) -> None:
        headlines = ["Company announces quarterly dividend"]
        score, conf = keyword_score(headlines)
        assert score == 0.0

    def test_confidence_increases_with_sentiment_words(self) -> None:
        low = keyword_score(["Company announces dividend"])
        high = keyword_score(["Stock surges, beats estimates, record profit, bullish"])
        assert high[1] > low[1]


class TestLabel:
    def test_bullish(self) -> None:
        assert _label(0.5) == "bullish"

    def test_bearish(self) -> None:
        assert _label(-0.5) == "bearish"

    def test_neutral(self) -> None:
        assert _label(0.0) == "neutral"


@pytest.mark.asyncio
async def test_analyze_sentiment_uses_keyword_when_llm_unavailable() -> None:
    items = [NewsItem(title="AAPL beats earnings, surges", publisher="test")]
    with (
        patch(
            "app.sentiment.service.fetch_news",
            new=AsyncMock(return_value=items),
        ),
        patch("app.sentiment.service.llm_score", new=AsyncMock(return_value=None)),
    ):
        result = await analyze_sentiment("AAPL")

    assert isinstance(result, SentimentResult)
    assert result.symbol == "AAPL"
    assert result.source == "keyword"
    assert result.article_count == 1
    assert result.score > 0  # bullish
    assert result.label == "bullish"
    assert len(result.top_headlines) == 1


@pytest.mark.asyncio
async def test_analyze_sentiment_uses_llm_when_available() -> None:
    items = [
        NewsItem(title="Mixed news for MSFT", publisher="test"),
        NewsItem(title="Analyst upgrades MSFT", publisher="test"),
    ]
    with (
        patch(
            "app.sentiment.service.fetch_news",
            new=AsyncMock(return_value=items),
        ),
        patch(
            "app.sentiment.service.llm_score",
            new=AsyncMock(return_value=(0.6, 0.85)),
        ),
    ):
        result = await analyze_sentiment("MSFT")

    assert result.source == "llm"
    assert result.score == 0.6
    assert result.confidence == 0.85
    assert result.label == "bullish"
    assert result.article_count == 2
