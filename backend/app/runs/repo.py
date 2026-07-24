"""Run repository — pure data-access on an injected async session.

The session is never created here; callers (FastAPI dependency, tests) pass it in.
These functions do not commit — transaction ownership stays with the caller so a
best-effort persist can be rolled back without affecting the response.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.runs.models import Run


async def create_run(session: AsyncSession, run: Run) -> Run:
    """Add a run, flush to obtain its id + server-defaults, return it."""
    session.add(run)
    await session.flush()
    await session.refresh(run)
    return run


async def list_runs(session: AsyncSession, limit: int = 50) -> list[Run]:
    """Most-recent-first history, capped."""
    stmt = select(Run).order_by(Run.created_at.desc()).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_run(session: AsyncSession, run_id: int) -> Run | None:
    """Single run by id, or None."""
    stmt = select(Run).where(Run.id == run_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
