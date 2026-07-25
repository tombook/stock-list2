"""Tests for the knowledge RAG layer."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.knowledge import service
from app.knowledge.embeddings import _tokenize, cosine_similarity, keyword_score


class TestKeywordScore:
    def test_match_returns_positive_score(self) -> None:
        score = keyword_score(
            "Tesla stock valuation",
            "Tesla is trading at high valuation with bullish momentum",
        )
        assert score > 0

    def test_no_match_returns_zero(self) -> None:
        score = keyword_score("hello world", "completely unrelated content")
        assert score == 0.0


class TestCosineSimilarity:
    def test_identical_vectors(self) -> None:
        v = [1.0, 0.5, 0.3]
        assert abs(cosine_similarity(v, v) - 1.0) < 1e-9

    def test_orthogonal_vectors(self) -> None:
        assert abs(cosine_similarity([1, 0], [0, 1])) < 1e-9


class TestTokenize:
    def test_strips_stopwords(self) -> None:
        tokens = _tokenize("the stock is trading at high valuation")
        assert "stock" in tokens
        assert "trading" in tokens
        assert "the" not in tokens
        assert "is" not in tokens


@pytest.mark.asyncio
async def test_ingest_creates_chunk(db_session: AsyncSession) -> None:
    chunk = await service.ingest(
        db_session, content="AAPL has strong fundamentals", source_type="test", symbol="AAPL"
    )
    assert chunk.id is not None
    assert chunk.symbol == "AAPL"


@pytest.mark.asyncio
async def test_search_returns_relevant_chunks(db_session: AsyncSession) -> None:
    await service.ingest(
        db_session,
        content="Apple reported strong iPhone revenue growth",
        source_type="test",
        symbol="AAPL",
    )
    await service.ingest(
        db_session,
        content="Tesla is facing EV demand challenges in China",
        source_type="test",
        symbol="TSLA",
    )
    results = await service.search(db_session, "Apple iPhone revenue", limit=3)
    assert len(results) >= 1
    apple_results = [r for r in results if r["symbol"] == "AAPL"]
    assert len(apple_results) >= 1


@pytest.mark.asyncio
async def test_search_filters_by_symbol(db_session: AsyncSession) -> None:
    await service.ingest(
        db_session,
        content="Apple earnings beat expectations",
        source_type="test",
        symbol="AAPL",
    )
    await service.ingest(
        db_session,
        content="Tesla deliveries miss estimates",
        source_type="test",
        symbol="TSLA",
    )
    results = await service.search(db_session, "earnings", limit=10, symbol="AAPL")
    for r in results:
        assert r["symbol"] in ("AAPL", None)


@pytest.mark.asyncio
async def test_ingest_analysis_result(db_session: AsyncSession) -> None:
    analysis = {
        "symbol": "AAPL",
        "analysts": {"technical": {"signal": "bullish", "confidence": 0.8}},
        "portfolio_manager": {"action": "buy", "confidence": 0.7},
    }
    chunk = await service.ingest_analysis_result(db_session, "AAPL", analysis)
    assert chunk.id is not None
    assert chunk.source_type == "analysis"
    assert chunk.symbol == "AAPL"
