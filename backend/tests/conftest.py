"""Pytest configuration. Keeps unit tests free of network/DB by default."""

from __future__ import annotations

import pytest

# pytest-asyncio runs in auto mode (see pyproject.toml) so async tests need no marker.


@pytest.fixture(autouse=True)
def _clear_market_cache() -> None:
    """Reset the market-data TTL cache between tests so they stay independent."""
    from app.marketdata import service

    service._quote_cache.clear()
    service._bars_cache.clear()
