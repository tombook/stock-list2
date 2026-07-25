"""Knowledge service — store analysis results and retrieve relevant context."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.knowledge.embeddings import score_similarity
from app.knowledge.models import KnowledgeChunk


async def ingest(
    session: AsyncSession,
    content: str,
    source_type: str,
    symbol: str | None = None,
    relevance: float = 1.0,
) -> KnowledgeChunk:
    chunk = KnowledgeChunk(
        symbol=symbol.upper() if symbol else None,
        source_type=source_type,
        content=content,
        relevance=relevance,
    )
    session.add(chunk)
    await session.flush()
    return chunk


async def search(
    session: AsyncSession,
    query: str,
    limit: int = 5,
    symbol: str | None = None,
) -> list[dict]:
    """Retrieve top-N most relevant knowledge chunks for a query."""
    stmt = select(KnowledgeChunk)
    if symbol:
        stmt = stmt.where(
            (KnowledgeChunk.symbol == symbol.upper()) | (KnowledgeChunk.symbol.is_(None))
        )
    stmt = stmt.order_by(KnowledgeChunk.created_at.desc()).limit(100)

    result = await session.execute(stmt)
    chunks = list(result.scalars().all())

    if not chunks:
        return []

    scored = []
    for chunk in chunks:
        score = await score_similarity(query, chunk.content)
        weighted = score * chunk.relevance
        scored.append((weighted, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)

    return [
        {
            "id": chunk.id,
            "symbol": chunk.symbol,
            "source_type": chunk.source_type,
            "content": chunk.content,
            "score": round(score, 4),
        }
        for score, chunk in scored[:limit]
        if score > 0.01
    ]


async def ingest_analysis_result(
    session: AsyncSession, symbol: str, analysis: dict
) -> KnowledgeChunk:
    """Store a multi-agent analysis result for future retrieval."""
    import json

    content = json.dumps(analysis, default=str, indent=2)[:5000]
    return await ingest(
        session,
        content=content,
        source_type="analysis",
        symbol=symbol,
        relevance=0.9,
    )
