"""Domain error types and a single place that maps them to HTTP responses."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class DomainError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class NotFoundError(DomainError):
    def __init__(self, message: str = "not found") -> None:
        super().__init__(message, 404)


class UpstreamError(DomainError):
    """A remote data source or LLM provider failed."""

    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message, status_code)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def _handle_domain(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"error": exc.message})
