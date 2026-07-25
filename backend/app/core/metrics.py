"""Prometheus metrics for the trading-research platform.

Exposes /metrics endpoint with HTTP request counts, latencies,
and LLM token usage. Lightweight — no middleware overhead.
"""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware

REQUESTS = Counter(
    "stocklist2_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)

LATENCY = Histogram(
    "stocklist2_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
)

LLM_TOKENS = Counter(
    "stocklist2_llm_tokens_total",
    "LLM tokens consumed",
    ["model", "kind"],  # kind: prompt | completion
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Record request count + latency for every HTTP request."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start

        # Skip /metrics itself to avoid infinite recursion
        if request.url.path == "/metrics":
            return response

        path = self._normalize_path(request.url.path)
        status = str(response.status_code)
        REQUESTS.labels(method=request.method, path=path, status=status).inc()
        LATENCY.labels(method=request.method, path=path).observe(elapsed)
        return response

    @staticmethod
    def _normalize_path(path: str) -> str:
        """Replace dynamic path segments with placeholders to avoid cardinality explosion."""
        parts = path.split("/")
        normalized = []
        for part in parts:
            if part.isdigit() or len(part) == 36:  # numeric or UUID
                normalized.append("{id}")
            else:
                normalized.append(part)
        return "/".join(normalized) or "/"


def record_llm_tokens(model: str, prompt_tokens: int, completion_tokens: int) -> None:
    """Call from LLM client to record token usage per request."""
    if prompt_tokens:
        LLM_TOKENS.labels(model=model, kind="prompt").inc(prompt_tokens)
    if completion_tokens:
        LLM_TOKENS.labels(model=model, kind="completion").inc(completion_tokens)


def metrics_response() -> Response:
    """Return the /metrics response with proper content type."""
    from fastapi.responses import Response

    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
