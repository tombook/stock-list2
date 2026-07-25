"""WebSocket connection registry + periodic quote broadcaster.

Each connected client subscribes to a set of symbols. A background task
polls quotes at a configurable interval and pushes updates to all subscribers.
"""

from __future__ import annotations

import asyncio
import json

from fastapi import WebSocket

from app.core.logging import get_logger
from app.marketdata import service as market_service

_log = get_logger(__name__)

PUSH_INTERVAL_SECONDS = 5.0

_clients: dict[WebSocket, set[str]] = {}
_lock = asyncio.Lock()
_broadcast_task: asyncio.Task[None] | None = None


async def register(websocket: WebSocket, symbols: set[str]) -> asyncio.Task[None]:
    """Register a client and start the broadcaster if needed."""
    async with _lock:
        _clients[websocket] = symbols.copy()
        _log.info("ws_client_connected", symbols=list(symbols))

    global _broadcast_task
    if _broadcast_task is None or _broadcast_task.done():
        _broadcast_task = asyncio.create_task(_broadcast_loop())
    return _broadcast_task


async def unregister(websocket: WebSocket) -> None:
    async with _lock:
        _clients.pop(websocket, None)
        _log.info("ws_client_disconnected", remaining=len(_clients))

    async with _lock:
        if not _clients and _broadcast_task and not _broadcast_task.done():
            _broadcast_task.cancel()


async def update_symbols(websocket: WebSocket, symbols: set[str]) -> None:
    async with _lock:
        _clients[websocket] = symbols.copy()


async def _collect_symbols() -> set[str]:
    async with _lock:
        all_syms: set[str] = set()
        for syms in _clients.values():
            all_syms.update(syms)
    return all_syms


async def _broadcast_loop() -> None:
    """Periodically fetch quotes for all subscribed symbols and push to clients."""
    while True:
        try:
            symbols = await _collect_symbols()
            if symbols:
                updates: dict[str, dict] = {}
                for sym in symbols:
                    try:
                        quote = await market_service.get_quote(sym)
                        updates[sym] = {
                            "symbol": quote.symbol,
                            "price": quote.price,
                            "change_pct": quote.change_pct,
                            "source": quote.source,
                        }
                    except Exception as exc:
                        updates[sym] = {"symbol": sym, "error": str(exc)}

                payload = json.dumps({"type": "quotes", "data": updates})

                async with _lock:
                    disconnected = []
                    for ws in list(_clients.keys()):
                        try:
                            await ws.send_text(payload)
                        except Exception:
                            disconnected.append(ws)
                    for ws in disconnected:
                        _clients.pop(ws, None)

            await asyncio.sleep(PUSH_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            _log.info("broadcast_task_cancelled")
            raise
        except Exception as exc:
            _log.error("broadcast_loop_error", error=str(exc))
            await asyncio.sleep(PUSH_INTERVAL_SECONDS)
