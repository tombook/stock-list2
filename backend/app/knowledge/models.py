"""Knowledge chunk ORM — stores text + embedding for RAG retrieval."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class KnowledgeChunk(Base):
    """A chunk of text stored for semantic retrieval."""

    __tablename__ = "knowledge_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    source_type: Mapped[str] = mapped_column(String(32))
    content: Mapped[str] = mapped_column(Text)
    symbol: Mapped[str | None] = mapped_column(String(16), index=True, default=None)
    relevance: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
