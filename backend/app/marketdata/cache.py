"""A tiny in-process TTL cache. Good enough for the data layer's short-lived
quotes/bars caching; a Redis-backed cache can drop in behind the same interface."""

from __future__ import annotations

import time
from typing import Generic, TypeVar

T = TypeVar("T")


class TTLCache(Generic[T]):
    def __init__(self, ttl_seconds: float) -> None:
        self.ttl = ttl_seconds
        self._store: dict[str, tuple[float, T]] = {}

    def get(self, key: str) -> T | None:
        item = self._store.get(key)
        if item is None:
            return None
        ts, value = item
        if time.monotonic() - ts > self.ttl:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: T) -> None:
        self._store[key] = (time.monotonic(), value)

    def clear(self) -> None:
        self._store.clear()
