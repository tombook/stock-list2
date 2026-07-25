"""Application factory and ASGI entrypoint (`uvicorn app.main:app`)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    agent,
    backtest,
    health,
    knowledge,
    market,
    patterns,
    risk,
    runs,
    screener,
    strategies,
    trading,
    watchlist,
    ws,
)
from app.core.auth import require_api_key
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.metrics import PrometheusMiddleware, metrics_response
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
    app.add_middleware(PrometheusMiddleware)

    # /health and /metrics are unauthenticated (infrastructure endpoints).
    app.include_router(health.router)

    @app.get("/metrics", include_in_schema=False)
    async def metrics() -> Response:
        return metrics_response()  # type: ignore[return-value]

    # All other API routes require API key when settings.api_key is set.
    api_deps = [Depends(require_api_key)]
    app.include_router(market.router, dependencies=api_deps)
    app.include_router(agent.router, dependencies=api_deps)
    app.include_router(backtest.router, dependencies=api_deps)
    app.include_router(runs.router, dependencies=api_deps)
    app.include_router(watchlist.router, dependencies=api_deps)
    app.include_router(screener.router, dependencies=api_deps)
    app.include_router(trading.router, dependencies=api_deps)
    app.include_router(risk.router, dependencies=api_deps)
    app.include_router(knowledge.router, dependencies=api_deps)
    app.include_router(strategies.router, dependencies=api_deps)
    app.include_router(patterns.router, dependencies=api_deps)
    app.include_router(ws.router, dependencies=api_deps)
    return app


app = create_app()
