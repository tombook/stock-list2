"""Broker factory — returns the configured broker or raises UpstreamError.

Centralized credential check + adapter selection. Each broker implements the
Broker protocol (place_order, cancel_order, get_account, get_positions).
"""

from __future__ import annotations

from app.core.errors import UpstreamError
from app.trading.brokers.base import Broker


def get_broker() -> Broker:
    """Return the active broker. Currently only Alpaca is wired."""
    s = _settings()
    if s.alpaca_api_key and s.alpaca_secret_key:
        from app.trading.brokers.alpaca import AlpacaBroker

        return AlpacaBroker()
    raise UpstreamError("no broker configured (set ALPACA_API_KEY/ALPACA_SECRET_KEY)", 400)


def _settings():
    from app.core.settings import get_settings

    return get_settings()
