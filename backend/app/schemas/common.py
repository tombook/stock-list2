"""Shared API response schemas."""

from __future__ import annotations

from typing import TypedDict


class DependencyStatus(TypedDict):
    status: str
    detail: str | None


class HealthResponse(TypedDict):
    status: str
    version: str
    dependencies: dict[str, DependencyStatus]
