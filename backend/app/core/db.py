"""Database layer — a single async engine for the whole process.

This is the fix for the original project's recurring bug: DB connection config
copied into 9+ modules, several hard-coding the wrong port. Here there is exactly
one engine, built from the single Settings source. Everything else takes a session
via the get_session dependency.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass

from app.core.settings import get_settings


class Base(MappedAsDataclass, DeclarativeBase):
    """Declarative base shared by every ORM model in the app."""


_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        s = get_settings()
        _engine = create_async_engine(
            s.db_dsn,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(get_engine(), expire_on_commit=False)
    return _session_factory


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding an async session."""
    async with get_session_factory()() as session:
        yield session


async def ping() -> bool:
    """Best-effort liveness probe for the database."""
    try:
        async with get_session_factory()() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
