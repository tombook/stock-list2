"""Application factory and ASGI entrypoint (`uvicorn app.main:app`)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import agent, backtest, health, knowledge, market, patterns, risk, runs, screener, strategies, trading, watchlist, ws
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.settings import get_settings


@asynccontextmanager
async def _lifespan(_: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="stock-list2", version="0.1.0", lifespan=_lifespan)

    origins = settings.cors_list or ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(health.router)
    app.include_router(market.router)
    app.include_router(agent.router)
    app.include_router(backtest.router)
    app.include_router(runs.router)
    app.include_router(watchlist.router)
    app.include_router(screener.router)
    app.include_router(trading.router)
    app.include_router(risk.router)
    app.include_router(knowledge.router)
    app.include_router(strategies.router)
    app.include_router(patterns.router)
    app.include_router(ws.router)
    return app


app = create_app()
