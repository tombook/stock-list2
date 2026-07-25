"""Pytest configuration.

The app holds one process-wide asyncpg engine. pytest-asyncio (auto mode) gives
each test its own event loop, which would invalidate that engine after the first
test. The autouse ``_reset_engine`` fixture drops the engine per test so it is
recreated on the current loop; DB-backed tests create their tables via
``db_session`` and truncate ``runs`` on teardown for isolation.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture(autouse=True)
def _clear_market_cache() -> None:
    """Reset the market-data TTL cache between tests so they stay independent."""
    from app.marketdata import service

    service._quote_cache.clear()
    service._bars_cache.clear()


@pytest.fixture(autouse=True)
async def _reset_engine() -> AsyncIterator[None]:
    """Drop the process-wide engine so it binds to this test's event loop.

    Without this, the engine created on test 1's loop raises "Event loop is closed"
    when test 2 (a different loop) touches it. On teardown we also truncate the
    persisted tables so tests that persist via the real routers (not via db_session)
    stay isolated. Disposed last.
    """
    import app.core.db as db

    db._engine = None
    db._session_factory = None
    yield
    if db._engine is not None:
        from sqlalchemy.exc import SQLAlchemyError

        try:
            async with db.get_session_factory()() as cleanup:
                await cleanup.execute(text("DELETE FROM runs"))
                await cleanup.execute(text("DELETE FROM watchlist_items"))
                await cleanup.execute(text("DELETE FROM bars_cache"))
                await cleanup.execute(text("DELETE FROM trading_orders"))
                await cleanup.execute(text("DELETE FROM trading_positions"))
                await cleanup.execute(text("DELETE FROM trading_accounts"))
                await cleanup.commit()
        except SQLAlchemyError:
            pass  # tables may not exist (e.g. pure unit tests)
        await db._engine.dispose()
    db._engine = None
    db._session_factory = None


@pytest.fixture
async def db_session(_reset_engine: None) -> AsyncIterator[AsyncSession]:
    """Async session on a fresh engine; creates tables up front, truncates after."""
    from app.core.db import Base, get_engine, get_session_factory

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = get_session_factory()
    async with factory() as session:
        yield session

    async with factory() as cleanup:
        await cleanup.execute(text("DELETE FROM runs"))
        await cleanup.execute(text("DELETE FROM watchlist_items"))
        await cleanup.execute(text("DELETE FROM bars_cache"))
        await cleanup.execute(text("DELETE FROM trading_orders"))
        await cleanup.execute(text("DELETE FROM trading_positions"))
        await cleanup.execute(text("DELETE FROM trading_accounts"))
        await cleanup.commit()


@pytest.fixture
async def api_client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    """HTTP client wired to the app with get_session overridden to the test session."""
    from app.core.db import get_session
    from app.main import app

    async def _override() -> AsyncSession:
        return db_session

    app.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()
