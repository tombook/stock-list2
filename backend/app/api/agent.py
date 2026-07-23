"""Agent endpoint — POST /api/analyze streams the agent loop as Server-Sent Events.

Event types: `step`, `tool_call`, `tool_result`, `final`, `error`. Uses a plain
StreamingResponse (no extra dependency) with SSE framing.
"""

from __future__ import annotations

import json

from fastapi import APIRouter
from pydantic import BaseModel
from starlette.responses import StreamingResponse

from app.agent import loop

router = APIRouter(prefix="/api", tags=["agent"])


class AnalyzeRequest(BaseModel):
    prompt: str
    stream: bool = True


@router.post("/analyze")
async def analyze(req: AnalyzeRequest) -> StreamingResponse:
    async def gen():
        try:
            async for event in loop.run(req.prompt):
                yield f"event: {event['type']}\ndata: {json.dumps(event['data'], default=str)}\n\n"
        except Exception as exc:  # keep the stream alive; report as an error event
            yield f"event: error\ndata: {json.dumps({'message': str(exc)})}\n\n"
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
