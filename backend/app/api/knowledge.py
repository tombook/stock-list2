"""Knowledge API — ingest + search endpoints for RAG."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.knowledge import service

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]


class IngestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str = Field(min_length=1)
    source_type: str = "manual"
    symbol: str | None = None
    relevance: float = Field(default=1.0, ge=0, le=2)


class SearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1)
    limit: int = Field(default=5, ge=1, le=20)
    symbol: str | None = None


@router.post("/ingest")
async def ingest(req: IngestRequest, session: SessionDep) -> dict:
    chunk = await service.ingest(
        session,
        content=req.content,
        source_type=req.source_type,
        symbol=req.symbol,
        relevance=req.relevance,
    )
    await session.commit()
    return {"id": chunk.id, "stored": True}


@router.post("/search")
async def search(req: SearchRequest, session: SessionDep) -> dict:
    results = await service.search(session, req.query, req.limit, req.symbol)
    return {"results": results, "count": len(results)}
