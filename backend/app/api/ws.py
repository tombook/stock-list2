"""WebSocket endpoint — /ws/quotes for real-time quote streaming."""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ConfigDict

from app.stream import register, unregister, update_symbols

router = APIRouter()


class SubscribeMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: str  # "subscribe" | "unsubscribe"
    symbols: list[str]


@router.websocket("/ws/quotes")
async def quotes_ws(websocket: WebSocket) -> None:
    await websocket.accept()
    initial = {"AAPL", "MSFT", "GOOG"}
    symbols = set(initial)

    try:
        await websocket.send_json(
            {
                "type": "hello",
                "symbols": sorted(symbols),
                "push_interval_seconds": 5,
            }
        )
        await register(websocket, symbols)

        while True:
            msg = await websocket.receive_json()
            action = SubscribeMessage(**msg) if isinstance(msg, dict) else None
            if action is None:
                continue
            new_syms = {s.upper() for s in action.symbols}
            if action.action == "subscribe":
                symbols |= new_syms
            elif action.action == "unsubscribe":
                symbols -= new_syms
            await update_symbols(websocket, symbols)
            await websocket.send_json(
                {
                    "type": "subscribed",
                    "symbols": sorted(symbols),
                }
            )
    except WebSocketDisconnect:
        await unregister(websocket)
    except Exception:
        await unregister(websocket)
        try:
            await websocket.close()
        except Exception:
            pass
